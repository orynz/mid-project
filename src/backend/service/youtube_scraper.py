import yt_dlp, requests
from typing import List, Dict
from pathlib import Path
import tempfile, json
from shared.youtube_schema import (
    YouTubeInfo,
    YouTubeMetaData,
    YouTubeTimeLineTranscribe,
    YouTubeFullDetail,
    ChapterItem,
    SubtitleItem,
)
import agents.graph as llm
import asyncio
from fastapi import HTTPException
from pydub import AudioSegment  # 오디오 처리 라이브러리
import tempfile
import threading, asyncio

MAX_VIDEO_DURATION_SECODS = 30 * 60  # 1800초 = 30분


def _parse_vtt(text) -> List[Dict]:
    """ "vtt 파일 데이터 정제"""

    lines_data = []
    lines = text.split("\n")
    for i in range(len(lines)):
        if "-->" in lines[i]:
            timestamp = lines[i].strip()
            subtitle_text = ""

            # 다음 줄 존재 확인 함수
            if i + 1 < len(lines):
                subtitle_text = lines[i + 1].strip()

            if subtitle_text:
                lines_data.append({"timestamp": timestamp, "text": subtitle_text})

    return lines_data


from service.media_utils import audio_download, split_audio


async def async_get_video_transcribe_with_stt(video_id: str):
    """
    영상 오디오를 다운로드 후 Whisper STT를 이용해 자막 데이터를 생성/반환
    """
    from agents.graph import async_transcribe_chunks_with_local

    path = Path(__file__).parent.parent / "data/subtitles"
    path.mkdir(parents=True, exist_ok=True)
    target_path = path / f"{video_id}.json"

    # 기존 자막 파일이 존재하면 오디오 다운로드/변환 프로세스 스킵
    if target_path.exists():
        with open(target_path, "r", encoding="utf-8") as f:
            return json.load(f)

    base_path = Path(__file__).parent.parent / "data/audio"
    base_path.mkdir(parents=True, exist_ok=True)

    loop = asyncio.get_running_loop()

    try:
        print(f"[{video_id}] 오디오 다운로드 중...")
        out_file = await loop.run_in_executor(
            None, audio_download, base_path, video_id, "wav"
        )

        with tempfile.TemporaryDirectory() as tmpdirname:
            temp_dir_path = Path(tmpdirname)

            chunk_paths = await loop.run_in_executor(
                None, split_audio, out_file, temp_dir_path, 10
            )

            print(f"[{video_id}] Fast Whisper STT 변환 중...")
            transcript = await async_transcribe_chunks_with_local(video_id, chunk_paths)

        return transcript
    except Exception as e:
        print(f"[{video_id}] STT 변환 중 오류: {e}")
        return []


async def get_video_list(query: str, count: int = 3) -> List[YouTubeInfo]:
    """
    요청 갯수 만큼 유튜브 추천 영상을 가져온다.
    """
    ydl_opts = {
        "quiet": False,  # 로그 출력 유무
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,  # 영상 다운로드 안 함
        "extract_flat": False,  # 상세 정보(조회수, 챕터 등)까지 가져오기 위해 False 권장
        # IP 차단 방지
        "sleep_interval": 1,
        "max_sleep_interval": 5,
        "sleep_interval_requests": 1,
        "force_ipv4": True,  # YouTube는 IPv6 대역을 자주 차단하므로 IPv4 강제 사용
    }

    loop = asyncio.get_running_loop()

    try:
        # run_in_executor를 통해 yt_dlp 동기 호출 비동기화
        def fetch_info():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(f"ytsearch5:{query}", download=False)

        info = await loop.run_in_executor(None, fetch_info)

        yt_info_list = []
        for video in info.get("entries", []):
            video_id = video.get("id", "")

            if not video.get("playable_in_embed", True):  # 외부 재생금지
                continue

            if (
                video.get("availability") != "public"
            ):  # 비공개, 로그인 필요, 프리미엄 제외
                continue

            video_lenth = int(video.get("duration", 0))
            if video_lenth > MAX_VIDEO_DURATION_SECODS:
                continue

            transcript = await async_get_video_transcribe_with_stt(video_id)

            yt_info_list.append(
                YouTubeInfo(
                    video_id=video.get("id", ""),
                    title=video.get("title", ""),
                    url=video.get("webpage_url", ""),
                    description=video.get("description", ""),
                    thumbnail_url=video.get("thumbnail"),
                    duration=video.get("duration", 0),
                    chapters=[
                        ChapterItem(
                            start=_format_time(c.get("start_time", 0)),
                            title=c.get("title", ""),
                        )
                        for c in video.get("chapters") or []
                    ],
                    tags=video.get("tags") or [],
                    channel_name=video.get("uploader", ""),
                    time_subtitle=[
                        SubtitleItem(
                            start=t.get("start", "00:00"), text=t.get("text", "")
                        )
                        for t in transcript
                    ],
                )
            )

            if len(yt_info_list) == count:
                break

        return yt_info_list

    except Exception as e:
        print(f"영상 목록 로드 에러: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _mb(path: str | Path) -> float:
    """
    파일 용량 확인
    """
    return Path(path).stat().st_size / 1024 / 1024


def _ensure_dirs(*dirs: Path) -> None:
    """
    디렉터리가 없으면 생성
    """
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def _audio_download(path: str | Path, video_id: str) -> str:
    """
    유튜브 영상을 오디오로 변환하여 다운로드
    """

    path = Path(path)
    target_path = path / f"{video_id}.{ext}"

    if not target_path.exists():
        ydl_opts_download = {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": str(target_path.with_suffix("")),  # 확장자 제외
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            # IP 차단 방지
            "sleep_interval": 1,
            "max_sleep_interval": 5,
            "sleep_interval_requests": 1,
            "force_ipv4": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                }
            ],
            "postprocessor_args": {
                "ffmpeg": ["-ac", "1", "-ar", "16000", "-vn"]  # 모노 / 16K / video 제거
            },
            # 재시도
            "retries": 5,
            "fragment_retries": 5,
            "file_access_retries": 3,
            # 다운로드 안정성(영상 내부 조각 병렬 다운로드)
            "concurrent_fragment_downloads": 5,
        }

        with yt_dlp.YoutubeDL(ydl_opts_download) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
    return str(target_path)


async def _async_audio_download(path: str | Path, video_id: str):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _audio_download, path, video_id)


def _split_audio(
    file_path: str | Path, temp_dir: Path, chunk_minutes: int = 10
) -> list[Path]:
    """임시 폴더(temp_dir)에 오디오를 10분(기본값) 단위로 저장"""

    file_path = Path(file_path)
    audio = AudioSegment.from_wav(file_path)  # wav 파일 로드

    chunk_ms = chunk_minutes * 60 * 1000  # 초 → 밀리초 변환
    chunks = []

    for i in range(0, len(audio), chunk_ms):
        chunk = audio[i : i + chunk_ms]
        chunk_name = temp_dir / f"{file_path.stem}_chunk_{i//chunk_ms}.wav"
        chunk.export(chunk_name, format="wav")
        chunks.append(chunk_name)

    return chunks


async def _async_split_audio(
    file_path: str | Path, temp_dir: Path, chunk_minutes: int = 10
) -> list[Path]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, _split_audio, file_path, temp_dir, chunk_minutes
    )


async def _process_video(video_id, path):
    print(f"[{video_id}] 작업 시작...")

    out_file = await _async_audio_download(video_id=video_id, path=path)
    with (
        tempfile.TemporaryDirectory() as tmpdirname
    ):  # 임시 폴더를 생성하여 청크 작업 진행
        temp_dir_path = Path(tmpdirname)
        chunk_paths = await _async_split_audio(out_file, temp_dir_path)
        text_data = await llm.async_transcribe_chunks_with_local(video_id, chunk_paths)

    print(f"[{video_id}] 작업 완료!")
    return text_data


async def run_video_transcribe(video_ids, path):
    base_path = Path(__file__).parent / "audio"
    _ensure_dirs(base_path)
    tasks = [_process_video(video_id=id, path=path) for id in video_ids]
    return await asyncio.gather(*tasks)


def _format_time(seconds):
    """시간(초) -> 'MM:SS' 형식으로 변환"""

    # 몫(minutes)과 나머지(seconds)를 구함
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes:02}:{secs:02}"


def _parse_vtt(text) -> List[Dict]:
    """ "vtt 파일 데이터 정제"""

    lines_data = []

    lines = text.split("\n")
    for i in range(len(lines)):
        if "-->" in lines[i]:
            timestamp = lines[i].strip()
            text = lines[i + 1].strip()
            lines_data.append({"timestamp": timestamp, "text": text})
    print("------------------------------------------------------ >", lines_data)
    return lines_data


def get_transcribe(auto_subs):
    langs = ["ko", "en"]

    for lang in langs:
        # 해당 언어의 자막 리스트 가져오기 (일반 자막 우선)
        subs = auto_subs.get(lang)  # requested_subs.get(lang) or

        if subs:
            sub_url = ""

            for sub in subs:
                if sub.get("ext") == "srt":
                    sub_url = sub["url"]
                    print(f"[{lang}] vtt 자막 URL: {sub_url}")
                    break

            # 언어 파일 다운로드 및 파싱
            if sub_url:
                res = requests.get(sub_url)
                vtt_data = _parse_vtt(res.text)

                timeline = [
                    SubtitleItem(
                        # timestamp 추출 및 변환
                        start=(
                            lambda ts: f"{int(ts.split(':')[0]) * 60 + int(ts.split(':')[1]):02}:{int(float(ts.split(':')[2])):02}"
                        )(line["timestamp"].split(" --> ")[0]),
                        text=line["text"],
                    )
                    for line in vtt_data[1::2]
                ]

                return timeline


def get_video_summarize(script: str):
    return llm.summarize(content_category="IT", transcript=script, max_words=300)


# def get_video_metadata(video_id: str) -> YouTubeMetaData:
#     """유튜브 영상 메타 정보 반환"""

#     try:
#         url = f"https://www.youtube.com/watch?v={video_id}"

#         with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
#             info = ydl.extract_info(url, download=False)

#         return YouTubeMetaData(
#             video_id=info.get("id", ""),
#             title=info.get("title", ""),
#             channel_name=info.get("uploader", ""),
#             description=info.get("description", ""),
#             thumbnail_url=info.get("thumbnail"),
#             chapters=YouTubeChapters(data=info.get("chapters") or []),
#             tags=info.get("tags") or [],
#             url=url
#         )

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# import os
# from pathlib import Path

# # 현재 파일 위치 기준
# BASE_DIR = Path(__file__).resolve().parent
# SUBTITLE_DIR = BASE_DIR / "subtitles"

# SUBTITLE_DIR.mkdir(parents=True, exist_ok=True)

# def get_video_transcribe(video_id: str):
#     """유튜브 영상 자막 반환"""

#     # 테스트용 id
#     # "rb3ZYR_Q1po" - 챕터 없음, 자막 있음
#     # "LcPrSL4sEOc" - 챕터 있음, 자막 없음

#     langs = ["ko", "en"]
#     ydl_opts = {
#         "writesubtitles": True,        # 일반 자막
#         "writeautomaticsub": False,     # 자동 자막
#         "subtitleslangs": langs,
#         "subtitlesformat": "vtt",      # vtt 형식
#         "skip_download": True,
#         "quiet": False,                 # 로그 출력 유무
#         "outtmpl": str(SUBTITLE_DIR / "%(id)s.%(ext)s"),
#         'cookiefile': 'cookies.txt',  # 브라우저 연동 대신 파일 직접 지정
#         # # 실제 브라우저처럼 보이게 헤더 설정
#         # "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
#         # "referer": "https://www.google.com",
#         # "cookiesfrombrowser": ("chrome",),  # chrome, firefox, edge 등 본인이 쓰는 브라우저
#         'sleep_interval': 8,       # 요청 사이에 최소 8초 대기
#         'max_sleep_interval': 15,   # 8~15초 사이 랜덤하게 대기하여 봇 탐지 회피
#         'force_ipv4': True,        # YouTube는 IPv6 대역을 자주 차단하므로 IPv4 강제 사용
#     }

#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         ydl.download(f"https://www.youtube.com/watch?v={video_id}")
#         # info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)

#         # requested_subs = info.get('subtitles', {})      # 일반
#         # auto_subs = info.get('automatic_captions', {})  # 자동

#         # for lang in langs:
#         #     # 해당 언어의 자막 리스트 가져오기 (일반 자막 우선)
#         #     subs = requested_subs.get(lang) or auto_subs.get(lang)

#         #     if subs:
#         #         sub_url = ""

#         #         for sub in subs:
#         #             if sub.get('ext') == 'vtt':
#         #                 sub_url = sub['url']
#         #                 # 2. 현재 찾은 언어(lang)를 정확히 출력합니다.
#         #                 print(f"[{lang}] vtt 자막 URL: {sub_url}")
#         #                 break

#         #         if sub_url:
#         #             res = requests.get(sub_url)
#         #             vtt_data = _parse_vtt(res.text)

#         #             timeline = []
#         #             for line in vtt_data[1::2]:
#         #                 timestamp = line["timestamp"].split(" --> ")[0]
#         #                 h, m, s = timestamp.split(':')
#         #                 m = int(h) * 60 + int(m)
#         #                 timeline.append({
#         #                     "start": f"{int(m):02}:{int(float(s)):02}",
#         #                     "text": line["text"]
#         #                 })

#         #             return YouTubeTimeLineTranscribe(
#         #                 time_subtitle=timeline,
#         #             )
#     print(f"\n-------챕터 정보를 찾을 수 없습니다. 직접 구현 필요!")
#     return YouTubeTimeLineTranscribe(time_subtitle=[])


def get_video_chapter(video_id: str):
    """유튜브 영상 챕터 반환"""

    # 테스트용 id
    # "rb3ZYR_Q1po" - 챕터 없음, 자막 있음
    # "LcPrSL4sEOc" - 챕터 있음, 자막 없음

    with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
        info = ydl.extract_info(
            f"https://www.youtube.com/watch?v={video_id}", download=False
        )

    chapters = info.get("chapters") or []
    data = []
    # 자동 챕터를 제공하는 경우 (챕터의 제목이 영어인 경우가 있음)
    if len(chapters) > 0:

        data = [
            {"start": _format_time(c.get("start_time", 0)), "title": c.get("title", "")}
            for c in chapters
        ]
        print(f"\n-------챕터: {data}")

    # 챕터를 직접 구현
    else:
        print(f"\n-------챕터 정보를 찾을 수 없습니다. 직접 구현 필요!")

    return YouTubeChapters(data=data)


def get_video_full_detail(video_id: str):
    """유튜브 영상의 자막, 챕터, 메타 정보를 한 번에 반환"""

    # 테스트용 id
    # "rb3ZYR_Q1po" - 챕터 없음, 자막 있음
    # "LcPrSL4sEOc" - 챕터 있음, 자막 없음

    langs = ["ko", "en"]
    ydl_opts = {
        "writesubtitles": True,  # 일반 자막
        "writeautomaticsub": True,  # 자동 자막
        "subtitleslangs": langs,
        "subtitlesformat": "vtt",  # vtt 형식
        "skip_download": True,
        "quiet": False,  # 로그 출력 유무
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(
            f"https://www.youtube.com/watch?v={video_id}", download=False
        )

        # 자막
        requested_subs = info.get("subtitles", {})  # 일반
        auto_subs = info.get("automatic_captions", {})  # 자동

        sub_url = None
        for lang in langs:
            # 일반 자막을 먼저 확인하고, 없으면 자동 자막 리스트 사용
            subs_list = requested_subs.get(lang) or auto_subs.get(lang)

            if subs_list:  # 해당 언어의 자막 리스트가 존재하면
                # 리스트 안에서 VTT 형식 자막 URL 찾기
                for sub in subs_list:
                    if sub.get("ext") == "vtt":
                        sub_url = sub["url"]
                        print(f"\n-------[{lang}] vtt 자막 URL: {sub_url}")
                        break

            if sub_url:
                break  # 우선순위가 높은 언어의 자막을 찾았으므로 언어 검색 루프 전체 종료

        # 자막 요청
        timelines = []
        if sub_url:
            res = requests.get(sub_url)

            # 자막 파싱
            vtt_data = _parse_vtt(res.text)
            for line in vtt_data[1::2]:
                timestamp = line["timestamp"].split(" --> ")[0]
                h, m, s = timestamp.split(":")
                m = int(h) * 60 + int(m)
                timelines.append(
                    {"start": f"{int(m):02}:{int(float(s)):02}", "text": line["text"]}
                )
        else:
            print(f"\n-------자막 정보를 찾을 수 없습니다. 직접 구현 필요!")

        # 챕터

        chapter_data = info.get("chapters") or []  # ----> llm 통해서 작업
        chapters = [
            ChapterItem(
                start=_format_time(c.get("start_time", 0)),
                title=c.get("title", "제목 없음"),
            )
            for c in chapter_data
        ]

        # 자막
        timeLine_transcribe = YouTubeTimeLineTranscribe(time_subtitle=timelines)

        return YouTubeFullDetail(
            video_id=info.get("id", ""),
            title=info.get("title", ""),
            channel_name=info.get("uploader", ""),
            description=info.get("description", ""),
            thumbnail_url=info.get("thumbnail"),
            chapters=chapters,
            tags=info.get("tags") or [],
            url=info.get("webpage_url", ""),
            timeLine_transcribe=timeLine_transcribe,
        )
