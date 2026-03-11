import streamlit as st
from backend.shared.youtube_schema import YouTubeInfo

def init_session_state():
    if "selected_video" not in st.session_state:
        st.session_state.selected_video = None
    if "recommended_videos" not in st.session_state:
        st.session_state.recommended_videos = []
    if "video_start_time" not in st.session_state:
        st.session_state.video_start_time = 0
    if "top_search_input" not in st.session_state:
        st.session_state.top_search_input = ""
    if "pending_search" not in st.session_state:
        st.session_state.pending_search = ""

def change_video(selected_video):
    """추천 영상 카드를 클릭했을 때 즉시 상태를 업데이트하는 콜백 함수"""
    st.session_state.selected_video = selected_video
    st.session_state.video_start_time = 0

def set_video_time(time_str):
    """타임라인 클릭 시 영상 시작 시간을 변경하는 콜백 함수"""
    try:
        parts = time_str.split(":")
        if len(parts) == 2:
            seconds = int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        else:
            seconds = 0
        st.session_state.video_start_time = seconds
    except:
        st.session_state.video_start_time = 0

def trigger_search():
    if st.session_state.top_search_input:
        st.session_state.pending_search = st.session_state.top_search_input
