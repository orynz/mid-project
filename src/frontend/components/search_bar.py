import streamlit as st
import requests
from backend.shared.youtube_schema import YouTubeInfo
from config import API_URL
from utils.state_manager import trigger_search, change_video

def render_search_bar():
    st.title("👾 AI 학습 큐레이터")
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
