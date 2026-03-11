# 📕 유튜브 기반 학습 콘텐츠 큐레이션 서비스 (챗봇)
유튜브 영상(초기 타겟: AI 에이전트 개발)을 기반으로 사용자에게 맞춤형 학습 큐레이션 및 커리큘럼을 제공하는 대화형 인공지능 챗봇입니다. 사용자가 직접 영상을 찾고 복잡한 커리큘럼을 직접 구성하는 수고를 덜어주기 위해 설계되었습니다.

---

### `.env` 파일에 아래와 같이 필수 API 키들을 본인 환경에 맞게 입력해 주세요.
```text
# OpenAI API
OPENAI_API_KEY=

# LangSmith API
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_PROJECT=
LANGCHAIN_API_KEY=

# 타빌리 API
TAVILY_API_KEY=
```

---

### Docs
- [회의록](<Docs/Meeting Notes>)
- [Git & GitHub 협업 완벽 가이드](Docs/Guide/git-github-collaboration-guide.md)
- [ChromaDB와  FAISS 차이점t](<Docs/Guide/ChromaDB vs FAISS.md>)

---

### 환경 설정을 위한 파이썬 라이브러리 설치

```bash
pip install -U -r requirements.txt
pip check
```

---

## 파이썬 패키지 관리 UV

#### 설치

>-맥OS, 리눅스, WSL
>```bash
>curl -LsSf https://astral.sh/uv/install.sh | sh
>```

>윈도우
>```bash
>powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
>```

#### 가상환경 만들기
```bash
uv venv .venv
```

##### 프로젝트 초기화
```bash
uv init
```

#### 패키지 설치
```bash
uv add fastapi streamlit langchain openai
uv add -r requirements.txt
```

#### 프로젝트 폴더에 `pyproject.toml` 또는 `uv.lock` 파일이 있는 경우
```bash
uv sync
```

streamlit 실행
- `.env` 파일에 `PYTHONPATH=src` 추가 후 root 경로에서 다음 명령어 실행
```bash
uv run --env-file .env streamlit run src/frontend/app.py
```


```text
project
│
├ src
│   │
│   ├ backend
│   │   │
│   │   ├ api                # FastAPI 라우터
│   │   │   ├ youtube_router.py
│   │   │   └ chat_router.py
│   │   │
│   │   ├ service            # 비즈니스 로직
│   │   │   ├ youtube_service.py
│   │   │   ├ summary_service.py
│   │   │   └ quiz_service.py
│   │   │
│   │   ├ repository         # DB 접근 (DAO)
│   │   │   ├ youtube_repo.py
│   │   │   └ user_repo.py
│   │   │
│   │   ├ db
│   │   │   ├ session.py     # DB 연결
│   │   │   ├ models.py      # ORM 모델
│   │   │   └ schema.py      # Pydantic schema
│   │   │
│   │   ├ ai
│   │   │   ├ prompts        # 프롬프트 관리
│   │   │   │   ├ summary_prompt.py
│   │   │   │   ├ quiz_prompt.py
│   │   │   │   └ idea_prompt.py
│   │   │   │
│   │   │   ├ chains         # LangChain / Agent
│   │   │   │   ├ summary_chain.py
│   │   │   │   └ quiz_chain.py
│   │   │   │
│   │   │   └ llm.py         # LLM 설정
│   │   │
│   │   ├ shared             # 공통 데이터 구조
│   │   │   ├ youtube_schema.py
│   │   │   └ response_schema.py
│   │   │
│   │   ├ core               # 환경설정
│   │   │   ├ config.py
│   │   │   └ logging.py
│   │   │
│   │   └ main.py            # FastAPI 시작점
│   │
│   └ frontend
│       ├ pages
│       │   ├ video_detail.py
│       │   └ quiz_page.py
│       │
│       └ app.py             # Streamlit 메인
│
├ data                       # 캐시 / 저장 데이터
│   ├ subtitles
│   └ embeddings
│
├ tests
│
├ scripts
│
├ pyproject.toml
└ .env
```