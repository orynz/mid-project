# 📕 유튜브 기반 AI 학습 콘텐츠 큐레이션 서비스

> 유튜브 영상(초기 타겟: AI 에이전트 개발)을 기반으로 사용자에게 맞춤형 학습 큐레이션 및 RAG 기반 Q&A를 제공하는 대화형 AI 챗봇 서비스입니다.  
> 사용자가 직접 영상을 찾고 커리큘럼을 구성하는 수고를 덜어주기 위해 설계되었습니다.

---

## 🎯 주요 기능

| 기능 | 설명 |
|---|---|
| **영상 검색 & 추천** | 키워드 기반 유튜브 영상 검색 (yt-dlp) |
| **STT 자막 생성** | Faster Whisper를 이용한 오디오 → 자막 자동 변환 |
| **타임라인 요약** | GPT-4o-mini로 영상을 타임라인 챕터별 요약 |
| **RAG Q&A** | ChromaDB + 한국어 임베딩 모델로 영상 내 시점 기반 질의응답 |
| **퀴즈 생성** | 자막 기반 객관식 퀴즈 자동 생성 |
| **학습 노트 생성** | 자막 기반 학습 노트 자동 생성 |

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Frontend                      │
│  검색바 → 영상 플레이어 → 탭(요약/퀴즈/학습노트/RAG Q&A)    │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP
┌───────────────────────────▼─────────────────────────────────┐
│                     FastAPI Backend                         │
│                                                             │
│  ┌──────────────┐   ┌──────────────┐   ┌─────────────────┐  │
│  │YouTube 스크래│   │ STT 파이프라 │   │  LLM 에이전트   │  │
│  │퍼(yt-dlp)    │──▶│ 인(딥스피치/ │──▶│(LangGraph)      │  │
│  │              │   │ Faster Whisper)│ │ - 타임라인 요약 │  │
│  └──────────────┘   └──────────────┘   │ - 퀴즈 생성     │  │
│                                        │ - 학습노트 생성 │  │
│  ┌──────────────────────────────────┐  └─────────────────┘  │
│  │    RAG 시스템 (ChromaDB)         │                       │
│  │  ko-sroberta-multitask 임베딩    │                       │
│  │  자막 청크 → 벡터 → 시점 추천    │                       │
│  └──────────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 핵심 데이터 플로우

```
사용자 검색 쿼리
      │
      ▼
yt-dlp 영상 목록 조회 (최대 30분 영상 필터링)
      │
      ▼
yt-dlp 오디오 다운로드 (WAV / 16kHz / 모노)
      │
      ▼
pydub 오디오 청크 분할 (10분 단위)
      │
      ▼
Faster Whisper STT → 자막 JSON 저장 (캐싱)
      │
      ├──▶ ChromaDB 벡터 인덱싱
      │
      └──▶ GPT-4o-mini 요약 / 퀴즈 / 학습노트 생성
```

---

## 🗂️ 프로젝트 구조

```
mid_project/
│
├── src/
│   ├── backend/
│   │   ├── agents/
│   │   │   ├── graph.py          # STT(Faster Whisper), 타임라인 요약, 퀴즈/학습노트 생성
│   │   │   ├── nodes.py          # LangGraph 노드 정의
│   │   │   └── states.py         # 그래프 상태 스키마
│   │   │
│   │   ├── api/                  # FastAPI 라우터
│   │   │
│   │   ├── service/
│   │   │   ├── youtube_scraper.py  # 영상 검색, 오디오 다운로드, STT 파이프라인
│   │   │   ├── media_utils.py      # 오디오 다운로드 & 분할 유틸리티
│   │   │   └── keyword_validator.py
│   │   │
│   │   ├── vector/
│   │   │   └── vector_db.py      # ChromaDB RAG 시스템
│   │   │
│   │   ├── prompts/              # LLM 프롬프트 관리
│   │   ├── shared/               # Pydantic 스키마 (YouTubeInfo 등)
│   │   ├── db/                   # DB 세션, ORM 모델
│   │   └── main.py               # FastAPI 엔트리포인트
│   │
│   └── frontend/
│       ├── app.py                # Streamlit 메인
│       ├── components/
│       │   ├── sidebar.py
│       │   ├── search_bar.py
│       │   ├── video_player.py
│       │   ├── video_tabs.py
│       │   └── recommended_videos.py
│       └── utils/
│           └── state_manager.py  # Streamlit 세션 상태 관리
│
├── data/                         # 캐시 저장소
│   ├── audio/                    # 다운로드된 오디오(WAV)
│   ├── subtitles/                # STT 변환 자막 JSON
│   └── vector/data/chroma/       # ChromaDB 벡터 데이터
│
├── pyproject.toml
├── requirements.txt
└── .env
```

---

## ⚙️ 기술 스택

| 레이어 | 기술 |
|---|---|
| **Frontend** | Streamlit |
| **Backend** | FastAPI + Uvicorn |
| **LLM** | GPT-4o-mini (OpenAI) |
| **LLM 프레임워크** | LangChain + LangGraph |
| **STT** | Faster-Whisper (base 모델, CUDA) |
| **벡터 DB** | ChromaDB |
| **임베딩 모델** | `jhgan/ko-sroberta-multitask` (한국어) |
| **영상 처리** | yt-dlp, pydub |
| **패키지 매니저** | uv |
| **Python** | 3.11+ |

---

## 🚀 실행 방법

### 1. 사전 준비

`.env` 파일 생성 후 아래 키 값을 입력합니다.

```env
# OpenAI API
OPENAI_API_KEY=

# LangSmith (선택)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_PROJECT=
LANGCHAIN_API_KEY=

# Tavily (웹 검색, 선택)
TAVILY_API_KEY=

# Python 경로 설정 (필수)
PYTHONPATH=src
```

> ⚠️ **Faster Whisper STT** 기능은 CUDA GPU 환경에서 동작합니다. GPU가 없는 환경에서는 `graph.py`에서 `device="cpu"`, `compute_type="int8"`으로 변경이 필요합니다.

---

### 2. 패키지 설치 (uv 권장)

```bash
# uv 설치 (Windows)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 가상환경 생성 및 패키지 동기화
uv venv .venv
uv sync
```

또는 기존 pip 방식:

```bash
pip install -U -r requirements.txt
```

---

### 3. Streamlit 실행

```bash
uv run --env-file .env streamlit run src/frontend/app.py
```

---

## 🧠 핵심 모듈 설명

### STT 파이프라인 (`service/youtube_scraper.py`, `agents/graph.py`)

1. `yt-dlp`로 유튜브 오디오 다운로드 (WAV, 16kHz, 모노)
2. `pydub`으로 10분 단위 청크 분할
3. `Faster Whisper` 로컬 모델로 STT 수행 → `data/subtitles/{video_id}.json` 캐싱
4. GPU 동시 접근 방지를 위해 `threading.Lock` 적용

### RAG 시스템 (`vector/vector_db.py`)

- **임베딩**: `jhgan/ko-sroberta-multitask` (한국어 SRoBERTa)
- **벡터 스토어**: ChromaDB (로컬 퍼시스턴트)
- **기능**:
  - `index_video_transcript()` — 자막 청크 → 벡터 저장
  - `get_rag_answer()` — 특정 영상 내 Q&A (시점 포함)
  - `get_global_rag_recommendation()` — 전체 영상 대상 검색 + 추천

### LLM 에이전트 (`agents/graph.py`)

| 함수 | 역할 |
|---|---|
| `timeline_summarize()` | 자막 기반 타임라인 챕터 분할 + 요약 |
| `generate_quiz()` | 객관식 퀴즈 생성 |
| `generate_lecture_note()` | 학습 노트 생성 |

---

## 📚 관련 문서

- [회의록](docs/Meeting%20Notes/)
- [Git & GitHub 협업 가이드](docs/Guide/git-github-collaboration-guide.md)
- [ChromaDB vs FAISS 차이점](docs/Guide/ChromaDB%20vs%20FAISS.md)

---

## 🛠️ 개발 환경 참고

- Python `3.11+`
- CUDA 지원 GPU (Faster Whisper 사용 시)
- ffmpeg 설치 필요 (yt-dlp 오디오 변환 후처리)

```bash
# ffmpeg 설치 확인
ffmpeg -version
```