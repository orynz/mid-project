import streamlit as st
from config import API_URL
import requests

def render_sidebar():
    with st.sidebar:
        st.markdown('<div style="padding: 1rem 0; text-align: center;">', unsafe_allow_html=True)
        st.markdown('<h2 style="letter-spacing: -0.05em; margin-bottom: 0;">NAVIGATOR</h2>', unsafe_allow_html=True)
        st.caption("AI 기반 맞춤형 학습 도우미")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<h4>📂 NAVIGATION</h4>', unsafe_allow_html=True)
        if st.button("🏠 Home", width="stretch"):
            st.session_state.current_page = "search"
            st.session_state.current_video = None
            st.session_state.selected_video = None
            st.rerun()
            
        if st.button("📊 Global Report", width="stretch"):
            st.session_state.current_page = "global_report"
            st.rerun()

        st.markdown('<div style="margin: 1.5rem 0; height: 1px; background: rgba(255,255,255,0.1);"></div>', unsafe_allow_html=True)
        
        st.markdown('<h4>🕒 HISTORY</h4>', unsafe_allow_html=True)
        
        # 검색 기록 표시
        if st.session_state.search_history:
            for hist in reversed(st.session_state.search_history[-10:]):
                # 클릭 시 검색어로 다시 검색하게 유도하는 버튼 형태로 스타일링
                if st.button(f"🔍 {hist}", key=f"hist_{hist}", width="stretch"):
                    st.session_state.current_page = "search"
                    st.session_state.top_search_input = hist
                    st.session_state.pending_search = hist
                    st.rerun()
        else:
            st.info("검색 기록이 없습니다.")
            
        st.sidebar.markdown("---")
        st.sidebar.caption("© 2026 AI Video Insight")
