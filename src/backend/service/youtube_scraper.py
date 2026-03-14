import yt_dlp, requests
from typing import List, Dict
from pathlib import Path
import tempfile, json
from shared.youtube_schema import (
    YouTubeInfo,
    # YouTubeMetaData,
    # YouTubeTimeLineTranscribe,
    # YouTubeFullDetail,
    ChapterItem,
    SubtitleItem,
)
import agents.graph as llm
import asyncio
from fastapi import HTTPException
from pydub import AudioSegment  # 오디오 처리 라이브러리
import tempfile
import threading, asyncio

MAX_VIDEO_DURATION_SECONDS = 60 * 60   # 1시간
MIN_VIDEO_DURATION_SECONDS = 20 * 60   # 1800초 = 20분


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
        "sleep_interval": 0.2,
        "max_sleep_interval": 1,
        "sleep_interval_requests": 0.2,
        "force_ipv4": True,  # YouTube는 IPv6 대역을 자주 차단하므로 IPv4 강제 사용
    }

    loop = asyncio.get_running_loop()

    try:
        # run_in_executor를 통해 yt_dlp 동기 호출 비동기화
        def fetch_info():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(f"ytsearch10:{query}", download=False)

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
            if video_lenth > MAX_VIDEO_DURATION_SECONDS:
                continue
            if video_lenth < MIN_VIDEO_DURATION_SECONDS:
                continue
            transcript = await async_get_video_transcribe_with_stt(video_id)

            yt_info_list.append(
                YouTubeInfo(
                    video_id=video.get("id", ""),
                    title=video.get("title", ""),
                    url=video.get("webpage_url", ""),
                    viewCount=video.get("view_count", 0),
                    likeCount=video.get("like_count", 0),
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

def _format_time(seconds):
    """시간(초) -> 'MM:SS' 형식으로 변환"""

    # 몫(minutes)과 나머지(seconds)를 구함
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes:02}:{secs:02}"

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