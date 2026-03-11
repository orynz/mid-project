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
    
    # 이미 생성된 인스턴스가 있다면 새로 만들지 않고 반환
    if _vector_store_instance is not None:
        return _vector_store_instance
    
    # 한국어 문장 임베딩에 최적화된 모델 로드
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    
    # Chroma DB 연결 (경로와 컬렉션 이름 지정)
    _vector_store_instance = Chroma(
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME
    )
    return _vector_store_instance

def search_video_content(query, video_id, k=3):
    """
    특정 영상 내에서 쿼리에 맞는 내용을 검색하고 결과를 출력합니다.
    """
    vector_store = get_vector_store()
    
    # Semantic Search 수행 (video_id 필터링 포함)
    results = vector_store.similarity_search(
        query, 
        k=k, 
        filter={"video_id": video_id}
    )

    print(f"🔍 검색어: '{query}'")
    print(f"📂 DB 경로: {CHROMA_PERSIST_DIR}\n")

    if not results:
        print("검색 결과가 없습니다.")
        return

    for idx, doc in enumerate(results):
        # 메타데이터 추출
        vid = doc.metadata.get('video_id', video_id)
        # start_time이 없을 경우를 대비해 기본값 0 설정
        min, sec = str(doc.metadata.get('start_time', '00:0')).split(':')
        start_time = int(min) * 60 + int(sec)
        
        # 유튜브 타임라인 이동 링크 생성
        youtube_url = f"https://www.youtube.com/watch?v={vid}&t={start_time}s"
        
        print(f"[{idx+1}순위 검색 결과]")
        print(f"- 자막 내용: {doc.page_content}")
        print(f"- 재생 시점: {doc.metadata.get('start_time', '00:00')} -------------> {start_time}초")
        print(f"- 바로가기 링크: {youtube_url}\n")

def save_transcripts_to_db(file_path: str, video_id: str):
    """
    JSON 자막을 읽어 ChromaDB에 저장하며, 이미 존재하는 경우 건너뜁니다.
    """
    
    # 파일 존재 여부 확인
    if not os.path.exists(file_path):
        print(f"파일을 찾을 수 없습니다: {file_path}")
        return
    
    # 임베딩 모델 및 벡터 스토어 초기화 (기존 DB 연결)
    vector_store = get_vector_store()
    
    # 중복(기존 임베딩) 체크
    # where 필터를 사용해 해당 video_id를 가진 데이터가 있는지 확인합니다.
    existing_data = vector_store.get(where={"video_id": video_id})
    if existing_data['ids']:
        print(f"⏩ 이미 DB에 존재하는 영상입니다 (video_id: {video_id}). 임베딩을 건너뜁니다.")
        return

    print("⏳ 새로운 영상입니다. JSON 자막 데이터를 불러오고 파싱합니다...")
    
    documents = []

    # JSON 데이터 로드 및 Document 객체 생성
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            transcript_data = json.load(f)
        except json.JSONDecodeError:
            print("JSON 파일 형식이 올바르지 않습니다.")
            return

        # JSON 구조에 맞게 반복문 처리 (리스트 형태의 딕셔너리라고 가정)
        for item in transcript_data:
            # 주의: 실제 JSON 파일의 키 이름(time, start, text 등)에 맞게 아래 변수를 수정해야 합니다.
            # 예시 JSON 구조: [{"time": "01:23", "text": "자막 내용"}, ...]
            time_str = item.get("time", "00:00") 
            content = item.get("text", "")

            if not content:
                continue

            try:
                # 'MM:SS' 형식 파싱 및 초 단위 변환
                m, s = time_str.split(":")
                time_sec = int(m) * 60 + int(s)
            except ValueError:
                time_sec = 0 # 파싱 실패 시 기본값 0초

            doc = Document(
                page_content=content,
                metadata={
                    "video_id": video_id,
                    "start_time": time_sec
                }
            )
            documents.append(doc)

    if not documents:
        print("파싱된 문서가 없습니다. JSON 파일의 키(key) 설정을 확인해 주세요.")
        return

    print(f"✅ {len(documents)}개의 문서를 파싱했습니다. 인덱싱을 시작합니다...")

    # 고유 ID 생성 및 DB 저장
    ids = [f"{video_id}_chunk_{i}" for i in range(len(documents))]
    
    # add_documents를 사용하여 기존 벡터 스토어에 데이터 추가
    vector_store.add_documents(documents=documents, ids=ids)
    
    print(f"🎉 ChromaDB 인덱싱이 완료되었습니다! (저장 경로: {CHROMA_PERSIST_DIR})\n")

if __name__ == "__main__":
    # 검색 테스트 데이터
    target_video_id = "3R6vFdb7YI4"
    search_query = "리스트의 pop 함수 사용법"
    
    # 실행
    try:
        search_video_content(search_query, target_video_id)
    except Exception as e:
        print(f"오류 발생: {e}")