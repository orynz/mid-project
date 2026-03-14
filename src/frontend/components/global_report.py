import streamlit as st
from utils.markdown import convert_timestamps_to_links

def render_global_report():
    """글로벌 RAG 분석 리포트 렌더링"""
    if "global_rag_data" in st.session_state and st.session_state.global_rag_data:
        report = st.session_state.global_rag_data.get("report")
        if report:
            with st.container():
                st.markdown("""
                <div style="
                    background: rgba(var(--primary-rgb), 0.1); 
                    border-radius: 15px; 
                    padding: 25px; 
                    border: 1px solid rgba(var(--primary-rgb), 0.2);
                    margin-bottom: 30px;
                ">
                    <h3 style="margin-top: 0; color: var(--primary);">🧪 AI 심층 분석 리포트</h3>
                    <div style="opacity: 0.9; line-height: 1.6;">
                """, unsafe_allow_html=True)
                
                convert_timestamps_to_links(report, key_prefix="global_report")
                
                st.markdown("""
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("닫기", key="close_global_report"):
                    st.session_state.global_rag_data = None
                    st.rerun()
