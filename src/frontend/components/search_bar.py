import streamlit as st
import requests
from backend.shared.youtube_schema import YouTubeInfo
from config import API_URL
from utils.state_manager import trigger_search, change_video

def render_search_bar():
    st.title("👾 AI 학습 큐레이터")
    
    tab_keyword, tab_semantic = st.tabs(["키워드 기반 검색", "의미 기반 (글로벌) 검색"])
    
    with tab_keyword:
        st.text_input(
            "배우고 싶은 내용을 알려주세요",
            label_visibility="hidden",
            placeholder="예: 파이썬 기초 영상 추천해줘",
            key="top_search_input",
            on_change=trigger_search,
        )
        
        user_input = st.session_state.get("pending_search", "")
        if user_input:
            st.session_state.pending_search = ""
            with st.spinner("🔍 AI 튜터가 영상을 검색하고 분석하는 중입니다..."):
                res = requests.post(f"{API_URL}/video/search/{user_input}")

                if res.status_code == 200:
                    data = res.json()
                    video_list = [YouTubeInfo.model_validate(item) for item in data]
                    st.session_state.recommended_videos = video_list
                    print(video_list)
                    if video_list:
                        change_video(video_list[0])
                    st.rerun()
                elif res.status_code == 400:
                    error_data = res.json()
                    st.warning(
                        f"🚫 학습과 관련 없는 키워드입니다: {error_data.get('detail', '다시 시도해 주세요.')}"
                    )
                else:
                    st.error(f"오류: {res.text}")
                    
    with tab_semantic:
        st.markdown("### 🌐 글로벌 RAG 검색")
        st.write("인덱싱된 전체 유튜브 영상 데이터를 대상으로 의미 있는 정보를 찾아 추천해 드립니다.")
        
        global_rag_question = st.text_input("질문 내용", placeholder="React와 Vue 비교해줘", key="global_rag_question_input")
        
        if st.button("의미 기반 검색 진행", key="btn_global_rag_search"):
            if not global_rag_question:
                st.warning("질문을 입력해주세요.")
            else:
                with st.spinner("🧠 전체 벡더 DB에서 관련된 내용을 검색하고 답변을 생성하는 중입니다..."):
                    payload = {"question": global_rag_question}
                    try:
                        res = requests.post(f"{API_URL}/video/rag/global", json=payload)
                        if res.status_code == 200:
                            data = res.json()
                            st.success("✨ 검색이 완료되었습니다!")
                            st.markdown(f"**답변:**\n\n{data.get('answer', '답변을 생성하지 못했습니다.')}")
                            
                            recommendations = data.get('recommendations', [])
                            if recommendations:
                                st.markdown("#### 📺 관련 영상 추천")
                                for rec in recommendations:
                                    vid = rec.get("video_id")
                                    st_time = rec.get("start_time")
                                    text = rec.get("text")
                                    
                                    with st.expander(f"비디오 ID: {vid} (타임라인: {st_time})"):
                                        st.write(f"**관련 내용:** {text}")
                                        
                                        # 타임라인을 초 단위로 변환해 YouTube 링크에 연결
                                        sec = 0
                                        try:
                                            parts = str(st_time).split(":")
                                            if len(parts) == 2:
                                                sec = int(parts[0]) * 60 + int(parts[1])
                                            elif len(parts) == 3:
                                                sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                                            else:
                                                sec = int(st_time)
                                        except:
                                            pass
                                            
                                        st.markdown(f"[여기부터 영상 보러가기](https://www.youtube.com/watch?v={vid}&t={sec}s)")
                        else:
                            st.warning(f"검색 중 문제가 발생했습니다: {res.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("백엔드 서버에 연결할 수 없습니다.")
