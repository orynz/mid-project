import sys
import os

# 백엔드 모듈 임포트를 위해 상위 디렉토리를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from backend.shared.youtube_schema import YouTubeInfo

from utils.state_manager import init_session_state
from components.sidebar import render_sidebar
from components.search_bar import render_search_bar
from components.video_player import render_video_player
from components.video_tabs import render_video_tabs
from components.recommended_videos import render_recommended_videos

# -----------------------------
# 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="유튜브 기반 영상 추천 서비스", page_icon="🎓", layout="wide"
)

st.markdown(
    """
<style>
.scroll-box {
    height: 600px;
    overflow-y: auto;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 10px;
}
</style>
    """,
    unsafe_allow_html=True,
)

# 상태 초기화
init_session_state()

# 사이드바 렌더링
render_sidebar()

# 상단 검색바 렌더링
render_search_bar()

st.divider()

# 메인 레이아웃 구성
left_col, right_col = st.columns([1, 1])

if isinstance(st.session_state.selected_video, YouTubeInfo):
    with left_col:
        render_video_player(st.session_state.selected_video)

    with right_col:
        render_video_tabs(st.session_state.selected_video)

    # 추천 영상은 선택된 영상이 유효할 때, 추천 목록에 실 데이터가 있는 경우 렌더링
    valid_recommendations = [v for v in st.session_state.recommended_videos if isinstance(v, YouTubeInfo)]
    if valid_recommendations:
        render_recommended_videos()
