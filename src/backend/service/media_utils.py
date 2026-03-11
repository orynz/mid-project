from pathlib import Path
import tempfile
import yt_dlp
from pydub import AudioSegment


def ensure_dirs(*dirs: Path) -> None:
    """디렉터리가 없으면 생성"""
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def audio_download(path: str | Path, video_id: str, ext: str = "wav") -> str:
    """유튜브 영상을 오디오로 변환하여 다운로드"""
    path = Path(path)
    ensure_dirs(path)
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
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": f"{ext}",  # flac or wav
                }
            ],
            "postprocessor_args": {
                "ffmpeg": ["-ac", "1", "-ar", "16000", "-vn"]  # 모노 / 16K / video 제거
            },
            # 재시도
            "retries": 5,
            "fragment_retries": 5,
            "file_access_retries": 3,
            # 다운로드 안정성
            "concurrent_fragment_downloads": 3,
        }

        with yt_dlp.YoutubeDL(ydl_opts_download) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
    return str(target_path)


def split_audio(
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
