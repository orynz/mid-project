import json, re, time
import threading, asyncio
from pathlib import Path
from faster_whisper import WhisperModel

from langchain_community.document_loaders.blob_loaders import Blob
from langchain_community.document_loaders.parsers.audio import OpenAIWhisperParser

# from prompts.timeline_summaize_prompt import generate_prompt
from prompts.timeline_summaize_prompt import generate_prompt
from dotenv import load_dotenv

load_dotenv()


def _ensure_dirs(*dirs: Path) -> None:
    """
    디렉터리가 없으면 생성
    """
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------
# GPU 메모리 초과 방지: 모델을 한 번만 로드하고 Lock으로 보호
# ------------------------------------------------------------------
whisper_model = None
whisper_lock = threading.Lock()


def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        print("Faster Whisper 모델 로딩 중...")
        whisper_model = WhisperModel("base", device="cuda", compute_type="float16")
    return whisper_model


def transcribe_chunks_with_local(video_id, chunks):
    """Fast Whisper를 이용한 STT"""

    model = get_whisper_model()

    path = Path(__file__).parent.parent / "data" / "subtitles"
    _ensure_dirs(path)
    target_path = path / f"{video_id}.json"

    if target_path.exists():
        with open(target_path, "r", encoding="utf-8") as f:  # 자막 로드
            return json.load(f)

    transcripts = []
    offset = 0

    for chunk in chunks:
        with whisper_lock:  # 여러 쓰레드가 동시에 GPU를 점유하지 못하도록 Lock 사용
            segments, _ = model.transcribe(chunk)

        last_segment_end = 0
        for s in segments:
            start = s.start + offset
            minute, sec = divmod(int(start), 60)

            transcripts.append(
                {"start": f"{minute:02}:{sec:02}", "text": s.text.strip()}
            )
            last_segment_end = s.end

        offset += last_segment_end

    with open(target_path, "w", encoding="utf-8") as f:  # 자막 저장
        json.dump(transcripts, f, ensure_ascii=False, indent=2)

    return transcripts


async def async_transcribe_chunks_with_local(video_id, chunks):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, transcribe_chunks_with_local, video_id, chunks
    )


def timeline_summarize(transcript_data: str, max_words: int = 200) -> dict:
    """
    타임라인 기반 자막 데이터를 요약 + 챕터 분할하여 반환합니다.

    Args:
        transcript_data: 타임라인 기반 자막 텍스트 (예: "00:00) 안녕하세요.")
        max_words: 요약 최대 단어 수

    Returns:
        dict: {"summary": "요약 내용", "timeline": [{"start": "MM:SS", "title": "챕터 제목"}]}
    """

    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage

    prompt = generate_prompt(transcript_data=transcript_data, max_words=max_words)
    chat = ChatOpenAI(model="gpt-4o-mini").bind(response_format={"type": "json_object"})

    try:
        response = chat.invoke([HumanMessage(content=prompt.strip())])
        text = response.content.strip()
        result = json.loads(text)

        return {
            "summary": result.get("summary", ""),
            "timeline": result.get("timeline", []),
        }

    except Exception as e:
        print(f"타임라인 요약 중 오류 발생: {e}")
        return {
            "summary": "요약을 생성하지 못했습니다.",
            "timeline": [],
        }


def generate_quiz(transcript_data: str) -> dict:
    """
    LangChain을 사용하여 자막 데이터를 기반으로 퀴즈 JSON을 생성합니다.
    """
    from prompts.quiz_prompt import generate_prompt as quiz_prompt_gen
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage

    chat = ChatOpenAI(model="gpt-4o-mini", temperature=0.7).bind(
        response_format={"type": "json_object"}
    )
    prompt_str = quiz_prompt_gen(lecture_content=transcript_data)

    try:
        response = chat.invoke([HumanMessage(content=prompt_str)])
        return json.loads(response.content)
    except Exception as e:
        print(f"퀴즈 생성 중 오류 발생: {e}")
        return {"error": "퀴즈를 생성하지 못했습니다."}


def generate_lecture_note(transcript_data: str) -> dict:
    """
    LangChain을 사용하여 자막 데이터를 기반으로 학습 노트 JSON을 생성합니다.
    """
    from prompts.lecture_note_promp import generate_prompt as note_prompt_gen
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage

    chat = ChatOpenAI(model="gpt-4o-mini", temperature=0.7).bind(
        response_format={"type": "json_object"}
    )
    prompt_str = note_prompt_gen(transcript_data=transcript_data)

    try:
        response = chat.invoke([HumanMessage(content=prompt_str)])
        return json.loads(response.content)
    except Exception as e:
        print(f"학습노트 생성 중 오류 발생: {e}")
        return {"error": "학습 노트를 생성하지 못했습니다."}
