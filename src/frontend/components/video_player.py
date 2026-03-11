import streamlit as st
from datetime import timedelta

def render_video_player(info):
    st.subheader("📺 메인 영상")
    st.video(info.url, start_time=st.session_state.video_start_time)
    
    duration_str = str(timedelta(seconds=info.duration)) if info.duration else "알 수 없음"
    st.markdown(
        f"""
                #### 📘 {info.title}

                ##### 영상길이: {duration_str}
                ###### 채널명: {info.channel_name}
        """
    )
    st.markdown(
        ":violet-badge[🐣 초급] :orange-badge[:material/star: 중급] :gray-badge[👿 고급]"
    )
