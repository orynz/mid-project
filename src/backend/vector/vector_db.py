import os
import json
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# 현재 파일 위치 기준으로 data/chroma 폴더에 DB 저장
BASE_DIR = Path(__file__).parent
CHROMA_PERSIST_DIR = str(BASE_DIR / "data" / "chroma")
COLLECTION_NAME = "video_transcripts"
MODEL_NAME = "jhgan/ko-sroberta-multitask"

_vector_store_instance = None

def get_vector_store():
    """
    임베딩 모델을 로드하고 Chroma 벡터 스토어를 반환합니다.
    """
    global _vector_store_instance
    
    if _vector_store_instance is not None:
        return _vector_store_instance
    
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    
    _vector_store_instance = Chroma(
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME
    )
    return _vector_store_instance

def index_video_transcript(video_id: str, transcript_data: list):
    """
    메모리 상의 자막 리스트를 ChromaDB에 저장하며, 이미 존재하는 경우 건너뜁니다.
    """
    vector_store = get_vector_store()
    
    # 중복(기존 임베딩) 체크
    existing_data = vector_store.get(where={"video_id": video_id})
    if existing_data and existing_data.get('ids'):
        print(f"⏩ 이미 DB에 존재하는 영상입니다 (video_id: {video_id}). 인덱싱을 건너뜁니다.")
        return

    print("⏳ 새로운 영상입니다. 자막 데이터를 파싱합니다...")
    
    documents = []
    
    for item in transcript_data:
        # JSON 구조에 맞게 수정: {"start": "00:00", "text": "자막 내용"}
        time_str = item.get("start", "00:00") 
        content = item.get("text", "")

        if not content:
            continue

        doc = Document(
            page_content=content,
            metadata={
                "video_id": video_id,
                "start_time": time_str
            }
        )
        documents.append(doc)

    if not documents:
        print("파싱된 문서가 없습니다.")
        return

    print(f"✅ {len(documents)}개의 문서를 파싱했습니다. 인덱싱을 시작합니다...")

    ids = [f"{video_id}_chunk_{i}" for i in range(len(documents))]
    vector_store.add_documents(documents=documents, ids=ids)
    
    print(f"🎉 ChromaDB 인덱싱이 완료되었습니다!\n")

def get_rag_answer(query: str, video_id: str) -> str:
    """
    특정 영상 내에서 쿼리에 맞는 내용을 검색하고 LLM을 통해 답변을 생성합니다.
    """
    vector_store = get_vector_store()
    
    # 1. 문서 검색
    results = vector_store.similarity_search(
        query, 
        k=3, 
        filter={"video_id": video_id}
    )

    if not results:
        return "해당 영상에서 관련 있는 내용을 찾을 수 없습니다."

    # 2. 관련 문맥 추출
    context_texts = []
    for doc in results:
        context_texts.append(f"[{doc.metadata.get('start_time', '00:00')}] {doc.page_content}")
    
    context = "\n".join(context_texts)
    
    # 3. LLM을 통한 답변 생성
    from langchain_core.prompts import PromptTemplate
    from langchain_openai import ChatOpenAI
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    prompt = PromptTemplate.from_template(
        "사용자의 질문에 대해 아래에 제공된 영상 자막 문맥만을 기반으로 답변해 주세요.\n\n"
        "문맥:\n{context}\n\n"
        "질문: {query}\n\n"
        "답변(관련 시점을 반드시 [MM:SS] 또는 [HH:MM:SS] 형식으로 포함하여 상세히 작성):"
    )
    
    chain = prompt | llm
    res = chain.invoke({"context": context, "query": query})
    return res.content

def get_global_rag_recommendation(query: str, k: int = 5) -> dict:
    """
    모든 영상 데이터를 대상으로 쿼리에 맞는 내용을 검색하고 LLM을 통해 답변과 추천 폼을 함께 반환합니다.
    """
    vector_store = get_vector_store()
    
    # 1. 문서 검색 (필터 없음)
    results = vector_store.similarity_search(
        query, 
        k=k
    )

    if not results:
        return {"answer": "저장된 기록 중 관련 있는 영상을 찾을 수 없습니다.", "recommendations": []}

    # 2. 관련 문맥 및 추천 객체 추출
    context_texts = []
    recommendations = []
    
    for doc in results:
        vid = doc.metadata.get("video_id", "")
        st = doc.metadata.get("start_time", "00:00")
        text = doc.page_content
        context_texts.append(f"[비디오ID: {vid}, 타임라인: {st}] {text}")
        
        recommendations.append({
            "video_id": vid,
            "start_time": st,
            "text": text
        })
    
    context = "\n".join(context_texts)
    
    # 3. LLM을 통한 답변 생성
    from langchain_core.prompts import PromptTemplate
    from langchain_openai import ChatOpenAI
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    prompt = PromptTemplate.from_template(
        "사용자가 전체 영상 기록을 대상으로 질문했습니다. 아래에 제공된 검색된 영상 자막 문맥만을 기반으로 답변해 주세요.\n"
        "답변 내용에는 가급적 관련 정보가 위치한 비디오 ID와 타임라인(반드시 [MM:SS] 또는 [HH:MM:SS] 형식)을 명시하여 출처를 밝혀주세요.\n\n"
        "문맥:\n{context}\n\n"
        "질문: {query}\n\n"
        "답변:"
    )
    
    chain = prompt | llm
    res = chain.invoke({"context": context, "query": query})
    
    return {
        "answer": res.content,
        "recommendations": recommendations
    }