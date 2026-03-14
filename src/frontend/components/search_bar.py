import streamlit as st
import requests
from backend.shared.youtube_schema import YouTubeInfo
from config import API_URL
from utils.state_manager import trigger_search, change_video

def render_search_bar():
    st.markdown('<h1 style="font-size: 2.2rem; margin-bottom: 0.2rem; font-weight: 800; letter-spacing: -0.05em;">AI LEARNING HUB</h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([5, 1])
    
    with col1:
        st.text_input(
            "검색",
            label_visibility="collapsed",
            placeholder="예: 파이썬 데이터 분석 강의 추천해줘",
            key="top_search_input",
            on_change=trigger_search
        )
    
    with col2:
        use_deep_search = st.checkbox("🔍 심층", help="전체 지식 베이스를 검색하여 깊이 있는 답변을 생성합니다.")

    # 검색 실행 로직
    pending_query = st.session_state.get("pending_search", "")
    if pending_query:
        st.session_state.last_query = pending_query
        st.session_state.pending_search = ""
        
        if use_deep_search:
            # 글로벌 RAG 검색
            with st.spinner("🧠 심층 분석 중..."):
                payload = {"question": pending_query}
                try:
                    res = requests.post(f"{API_URL}/video/global-recommend", json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.global_rag_data = data
                        if pending_query not in st.session_state.search_history:
                            st.session_state.search_history.append(pending_query)
                                                    
                        st.rerun()
                except Exception as e:
                    st.error(f"Exception: {e}")
        else:
            # 키워드 검색
            with st.spinner("🔍 추천 영상 찾는 중..."):
                try:
                    res = requests.post(f"{API_URL}/video/search/{pending_query}")
                    if res.status_code == 200:
                        data = res.json()
                        video_list = [YouTubeInfo.model_validate(item) for item in data]
                        st.session_state.selected_video = video_list[0]
                        if pending_query not in st.session_state.search_history:
                            st.session_state.search_history.append(pending_query)
                        
                        if video_list not in st.session_state.recommended_videos:
                            st.session_state.recommended_videos = video_list
                            
                        st.rerun()
                    elif res.status_code == 400:
                        error_data = res.json()
                        st.warning(
                            f"🚫 학습과 관련 없는 키워드입니다: {error_data.get('detail', '다시 시도해 주세요.')}"
                        )
                    else:
                        st.error(f"오류: {res.text}")
                except Exception as e:
                    st.error(f"Exception: {e}")
                    

    # 결과 표시
    if st.session_state.get("global_rag_data"):
        data = st.session_state.global_rag_data
        with st.expander("✨ AI 심층 분석 리포트", expanded=True):
            st.markdown(data.get('answer', ''))
            if st.button("결과 닫기"):
                st.session_state.pop("global_rag_data")
                st.rerun()
