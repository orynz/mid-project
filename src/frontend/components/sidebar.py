import streamlit as st

def render_sidebar():
    with st.sidebar:
        st.markdown("#### 💬 채팅 기록")
        st.caption("기록이 없습니다.")
        st.markdown("---")
