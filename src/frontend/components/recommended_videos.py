import streamlit as st
from datetime import timedelta
from utils.state_manager import change_video

def render_recommended_videos():
    st.divider()
    st.subheader("🔎 추천 영상")

    cols = st.columns(3)

    for i, info in enumerate(st.session_state.recommended_videos):
        with cols[i % 3]: 
            with st.container(border=True):
                is_selected = st.session_state.selected_video.video_id == info.video_id
                
                # Duration formatting
                duration_str = str(timedelta(seconds=info.duration)) if info.duration else "N/A"
                
                # Title truncation
                display_title = info.title if len(info.title) <= 45 else info.title[:42] + "..."

                # Render Premium Card using Markdown for styling
                st.markdown(f"""
                <div class="video-card">
                    <img src="https://img.youtube.com/vi/{info.video_id}/mqdefault.jpg" style="width:100%">
                    <div style="font-weight:700; font-size:1rem; margin-bottom:4px; height:3em; overflow:hidden;">{display_title}</div>
                    <div style="color:var(--text-muted); font-size:0.85rem; margin-bottom:8px;">
                        👤 {info.channel_name} <br> ⏱️ {duration_str}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Button for interaction (Button must be outside the markdown for click handling)
                button_label = "✅ 선택됨" if is_selected else "▶️ 강의 시청"
                st.button(
                    button_label,
                    key=f"btn_{info.video_id}",
                    type="primary" if is_selected else "secondary",
                    width="stretch",
                    on_click=change_video,
                    args=(info,),
                )
