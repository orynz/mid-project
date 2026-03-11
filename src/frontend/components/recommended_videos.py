import streamlit as st
from datetime import timedelta
from utils.state_manager import change_video

def render_recommended_videos():
    st.divider()
    st.subheader("🔎 추천 영상")

    cols = st.columns(3)

    for i, info in enumerate(st.session_state.recommended_videos):
        with cols[i % 3]: 
            is_selected = st.session_state.selected_video.video_id == info.video_id

            with st.container(border=True):
                st.image(
                    f"https://img.youtube.com/vi/{info.video_id}/0.jpg", width="stretch"
                )

                display_title = (
                    info.title if len(info.title) <= 45 else info.title[:43] + "..."
                )
                st.markdown(f"**{display_title}**")

                duration_str = (
                    str(timedelta(seconds=info.duration))
                    if info.duration
                    else "알 수 없음"
                )
                st.caption(f"👤 **{info.channel_name}** | ⏱️ {duration_str}")

                if info.tags:
                    tags_html = " ".join([f"`#{tag}`" for tag in info.tags[:5]])
                    st.markdown(tags_html)
                else:
                    st.markdown("Unknown")

                button_type = "primary" if is_selected else "secondary"
                button_label = "✅ 선택 영상" if is_selected else "▶️ 재생하기"

                st.button(
                    button_label,
                    key=f"btn_{info.video_id}",
                    type=button_type,
                    use_container_width=True,
                    on_click=change_video,
                    args=(info,),
                )
