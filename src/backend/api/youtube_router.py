from shared.youtube_schema import (
    YouTubeInfo,
    YouTubeMetaData,
    YouTubeTimeLineTranscribe,
    YouTubeFullDetail,
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


@router.post("/search/{query}", response_model=list[YouTubeInfo])
async def get_video_infos(query: str):
    """
    검색 키워드가 학습/교육 관련인지 검증
    """
    validation = validate_learning_keyword(query)
    if not validation["is_learning"]:
        raise HTTPException(status_code=400, detail=validation["reason"])
    return await yt.get_video_list(query=query)


@router.post("/summarize/{transcript}", response_model=None)
async def get_video_summarize(transcript: str):
    """
    영상 스크립트를 기반으로 요약
    """
    return llm.summarize(content_category="IT", transcript=transcript, max_words=300)


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
