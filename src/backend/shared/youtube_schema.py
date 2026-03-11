from pydantic import BaseModel, Field
from typing import List, Optional
import re

# --- 하위 데이터 구조(Nested Models) 정의 ---

class SubtitleItem(BaseModel):
    """타임라인 자막 조각"""
    start: str = Field(description="시작 시간 (예: '00:00')")
    text: str = Field(description="자막 내용")

class ChapterItem(BaseModel):
    """챕터 정보 조각"""
    start: str = Field(description="시작 시간 (예: '00:00')")
    title: str = Field(description="챕터 제목")


# --- 메인 응답/요청 모델 정의 ---

class YouTubeInfo(BaseModel):
    """유튜브 기본 정보"""
    video_id: str = Field(description="영상 id")
    title: str = Field(description="영상 제목")
    url: str = Field(description="영상 url")
    channel_name: str = Field(description="채널")
    description: str = Field(description="설명")
    duration: int = Field(description="유튜브 영상 길이")
    thumbnail_url: Optional[str] = Field(default=None, description="썸네일")
    chapters: List[ChapterItem] = Field(default_factory=list, description="챕터 목록")
    tags: List[str] = Field(default_factory=list, description="태그 목록")
    time_subtitle: List[SubtitleItem] = Field(description="타임 자막", default=[])

    def get_full_transcript(self) -> str:
        """자막 텍스트를 반환
        
        Returns:
            str: 타임라인 기반 자막 텍스트 예 - "00:00) 안녕하세요."
        """
        return "\n".join(f"{line.start}) {line.text}" for line in self.time_subtitle)
        
    def parse_description(self):
        TAG_PATTERN = r"#\w+"
        TIMELINE_PATTERN = r"(\d{1,2}:\d{2})(?::\d{2})?\s+([^\n]+)"
        LINK_PATTERN = r"https?://[^\s]+|www\.[^\s]+"
        
        text = self.description
        
        tags: List[str] = re.findall(TAG_PATTERN, text)     # 태그 추출
        links: List[str] = re.findall(LINK_PATTERN, text)   # 링크 추출

        # 타임라인 추출
        timeline = []
        matches = re.findall(TIMELINE_PATTERN, text)
        for time, title in matches:
            timeline.append({
                "time": time,
                "title": title.strip()
            })
        
        # 제거
        cleaned = re.sub(TAG_PATTERN, "", text)
        cleaned = re.sub(TIMELINE_PATTERN, "", cleaned)
        cleaned = re.sub(LINK_PATTERN, "", cleaned)
        
        # 공백 정리
        cleaned = re.sub(r"\n{2,}", "\n\n", cleaned).strip()
        
        # 줄 단위 분리
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        summary = ""
        content = []
        cta = ""

        for line in lines:
            if "구독" in line or "좋아요" in line:
                cta = line

            elif summary == "":
                summary = line
                content.append(line)

            else:
                content.append(line)

        return {
            "tags": tags,
            "summary": summary,
            "links": links,
            "content": content,
            "timeline":timeline,
            "cta": cta
        }

class YouTubeMetaData(YouTubeInfo):
    """유튜브 메타 정보"""
    # channel_name: str = Field(description="채널")
    # description: str = Field(description="설명")
    # thumbnail_url: Optional[str] = Field(default=None, description="썸네일")
    # chapters: List[ChapterItem] = Field(default_factory=list, description="챕터 목록")
    # tags: List[str] = Field(default_factory=list, description="태그 목록")
    test: Optional[str] = Field(default=None, description="썸네일")
    
class YouTubeTimeLineTranscribe(BaseModel):
    """유튜브 타임라인 자막 정보"""
    # lang:str = Field(description="언어")
    time_subtitle: List[SubtitleItem] = Field(description="타임 자막")
    
    def get_full_transcript(self) -> str:
        """자막 텍스트를 반환
        
        Returns:
            str: 타임라인 기반 자막 텍스트 예 - "00:00) 안녕하세요."
        """
        return "\n".join(f"{line.start}) {line.text}" for line in self.time_subtitle)


    
class YouTubeFullDetail(YouTubeMetaData):
    """유튜브 메타정보, 챕터, 자막을 모두 포함하는 종합 데이터"""
    
    timeLine_transcribe:YouTubeTimeLineTranscribe = Field(description="타임라인 자막 - {'start': '00:00', 'text': '안녕하세요.'} ")
    
    def get_full_transcript(self) -> str:
        """자막 텍스트를 반환

        Returns:
            str: 타임라인 기반 자막 텍스트 예 - "00:00) 안녕하세요."
        """
        full_text = ""
        transcribe = self.timeLine_transcribe
        for line in transcribe.time_subtitle:
            full_text += f"{line['start']}) {line['text']}\n"
        return full_text