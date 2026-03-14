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
from components.global_report import render_global_report

# -----------------------------
# 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="Global AI Video Hub", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
<style>
.block-container {
    max-width: 80%; /* 화면의 80%만 사용 */
}
.scroll-box {
    height: 600px;
    overflow-y: auto;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 10px;
}
/* tertiary 타입 버튼의 글자색을 파란색으로, 배경은 투명하게 강제 적용 */
div[data-testid="stButton"] button[kind="tertiary"] {
    color: #007BFF !important;       /* 밝은 파란색 */
    background-color: transparent !important;
    padding: 2px 5px !important;    /* 간격 미세 조정 */
    border: none !important;
    margin-top: -10px;    /* 상단 여백 */
    margin-bottom: -10px; /* 하단 여백 */
    margin-left: 0px;   /* 좌측 여백 */
    margin-right: 0px;  /* 우측 여백 */
}

/* 마우스 호버 시 효과 (약간 더 진한 파란색) */
div[data-testid="stButton"] button[kind="tertiary"]:hover {
    color: #0056b3 !important;
    text-decoration: underline !important; /* 클릭 가능해 보이도록 밑줄 */
    background-color: transparent !important; /* 아주 연한 배경 */
    transform: scale(1.02);              /* 살짝 커지는 효과 */
    transition: all 0.2s ease;
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

# 글로벌 RAG 리포트 표시
render_global_report()

# 메인 레이아웃 구성
if isinstance(st.session_state.selected_video, YouTubeInfo):
    with st.container():
        left_col, right_col = st.columns([1, 1], gap="large")
        with left_col:
            render_video_player(st.session_state.selected_video)

        with right_col:
            render_video_tabs(st.session_state.selected_video)

    # 추천 영상은 선택된 영상이 유효할 때, 추천 목록에 실 데이터가 있는 경우 렌더링
    valid_recommendations = [v for v in st.session_state.recommended_videos if isinstance(v, YouTubeInfo)]
    if valid_recommendations:
        render_recommended_videos()
    else:
        st.info("제공되는 영상이 없습니다.")
else:
    # 선택된 영상이 없을 때의 메인 화면 디자인
    st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; padding: 40px; background: rgba(255, 255, 255, 0.03); border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.05);">
        <h2 style="margin-bottom: 20px;">🚀 시작하기</h2>
        <p style="font-size: 1.2rem; opacity: 0.8; margin-bottom: 30px;">
            위에 있는 검색창에 유튜브 URL을 입력하거나 궁금한 주제를 검색해 보세요.<br>
            AI 튜터가 영상 분석부터 퀴즈 생성까지 완벽하게 도와드립니다.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div style="height: 40px;"></div>', unsafe_allow_html=True)
    
    st.markdown("### ✨ 주요 기능")
    cols = st.columns(3)
    
    features = [
        ("📚", "학습 노트 생성", "핵심 내용을 마크다운으로 정리"),
        ("🤖", "대화형 AI 튜터", "영상 기반 Q&A 및 시점 추천"),
        ("✅", "퀴즈 및 과제", "학습 내용 복습용 퀴즈 생성")
    ]
    
    for i, (icon, title, desc) in enumerate(features):
        with cols[i]:
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #e5e7eb; height: 100%;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
                <h5 style="margin: 0; color: #1f2937;">{title}</h5>
                <p style="font-size: 0.85rem; color: #6b7280; margin-top: 0.5rem;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div style="height: 40px;"></div>', unsafe_allow_html=True)

    if st.session_state.recommended_videos:
        st.markdown(f"### '{st.session_state.last_query}' 검색 결과")
        
        for video in st.session_state.recommended_videos:
            with st.container():
                col_thumb, col_info = st.columns([1, 2])
                with col_thumb:
                    if video.thumbnail_url:
                        st.image(video.thumbnail_url, width="stretch")
                with col_info:
                    st.markdown(f"#### {video.title}")
                    st.markdown(f"**채널:** {video.channel_name}")
                    st.markdown(f"**길이:** {video.duration}초")
                    
                    if st.button("📺 강의 시작", key=f"play_{video.video_id}", type="primary"):
                        from utils.state_manager import change_video
                        change_video(video)
                        st.session_state.recommended_videos = [] # 결과 목록 초기화
                        st.rerun()
            st.markdown('<div style="margin: 1.5rem 0; height: 1px; background: rgba(0,0,0,0.05);"></div>', unsafe_allow_html=True)
    else:
        # 기본 대기 화면
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px; background: #f9fafb; border-radius: 20px; margin-top: 2rem;">
            <h2 style="color: #6366f1;">어떤 것을 배워볼까요?</h2>
            <p style="color: #6b7280; font-size: 1.1rem;">상단 검색창에 학습하고 싶은 주제를 입력해보세요.</p>
            <div style="margin-top: 2rem;">
                <span style="background: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem; color: #4b5563; margin: 0 5px; border: 1px solid #e5e7eb;">#AI Agent 개발</span>
                <span style="background: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem; color: #4b5563; margin: 0 5px; border: 1px solid #e5e7eb;">#Machine Learning</span>
                <span style="background: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem; color: #4b5563; margin: 0 5px; border: 1px solid #e5e7eb;">#Prompt Engineering</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('<div style="height: 60px;"></div>', unsafe_allow_html=True)
    st.caption("💡 Tip: 검색 결과에서 마음에 드는 영상을 선택하면 즉시 분석이 시작됩니다.")
