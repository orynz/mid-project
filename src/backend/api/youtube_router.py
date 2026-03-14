from shared.youtube_schema import (
    YouTubeInfo,
    # YouTubeMetaData,
    # YouTubeTimeLineTranscribe,
    # YouTubeFullDetail,
)
from pydantic import BaseModel
from agents import graph as llm
from service import youtube_scraper as yt
from service.keyword_validator import validate_learning_keyword
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/video", tags=["youtube", "video"])


class TranscriptRequest(BaseModel):
    """
    자막 데이터 요청 모델
    """

    transcript: str


class RagRequest(BaseModel):
    """
    RAG 검색 API 요청 모델
    """
    video_url: str = ""
    question: str
    video_id: str = ""

class GlobalRagRequest(BaseModel):
    """
    글로벌 RAG 검색 API 요청 모델
    """
    question: str

@router.post("/search/{query}", response_model=list[YouTubeInfo])
async def get_video_infos(query: str):
    """
    검색 키워드가 학습/교육 관련인지 검증
    """
    validation = validate_learning_keyword(query)
    if not validation["is_learning"]:
        raise HTTPException(status_code=400, detail=validation["reason"])
    return await yt.get_video_list(query=query)


@router.post("/timeline-summary")
async def get_timeline_summary(req: TranscriptRequest):
    """
    자막 데이터를 기반으로 타임라인 요약 + 챕터 분할 반환
    출력: {"summary": "...", "timeline": [{"start": "MM:SS", "title": "..."}]}
    """
    if not req.transcript.strip():
        raise HTTPException(status_code=400, detail="자막 데이터가 비어 있습니다.")
    return llm.timeline_summarize(transcript_data=req.transcript)

@router.post("/quiz")
async def get_quiz(req: TranscriptRequest):
    """
    자막 데이터를 기반으로 퀴즈를 생성합니다.
    """
    if not req.transcript.strip():
        raise HTTPException(status_code=400, detail="자막 데이터가 비어 있습니다.")
    return llm.generate_quiz(transcript_data=req.transcript)

@router.post("/lecture-note")
async def get_lecture_note(req: TranscriptRequest):
    """
    자막 데이터를 기반으로 학습 노트를 생성합니다.
    """
    if not req.transcript.strip():
        raise HTTPException(status_code=400, detail="자막 데이터가 비어 있습니다.")
    return llm.generate_lecture_note(transcript_data=req.transcript)

@router.post("/rag")
async def ask_rag(req: RagRequest):
    """
    RAG 파이프라인 Q&A 처리를 위한 백엔드 엔드포인트
    """
    from vector.vector_db import get_rag_answer, index_video_transcript
    
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="질문(question)이 필요합니다.")
    
    # 1) 로컬 자막 파일 확인 (없으면 Whisper STT로 생성) 및 인덱싱
    try:
        transcript_data = await yt.async_get_video_transcribe_with_stt(req.video_id)
        if transcript_data:
            index_video_transcript(req.video_id, transcript_data)
        else:
            print(f"[{req.video_id}] 자막 데이터를 생성/로드하지 못했습니다.")
    except Exception as e:
        print(f"자막 인덱싱 실패: {e}")
            
    # 2) RAG 파이프라인 연동
    answer = get_rag_answer(query=req.question, video_id=req.video_id)
    return {"answer": answer}

@router.post("/global-recommend")
async def ask_global_recommend(req: GlobalRagRequest):
    """
    모든 인덱싱된 영상을 대상으로 RAG 검색 수행 (Global Knowledge Base)
    """
    from vector.vector_db import get_global_rag_recommendation
    
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="질문(question)이 필요합니다.")
        
    result = get_global_rag_recommendation(query=req.question, k=5)
    
    # 프론트엔드 사이드바에서 기대하는 키 'recommendation'으로 반환
    return {"recommendation": result.get("answer", "추천을 생성할 수 없습니다.")}
