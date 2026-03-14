import streamlit as st
from datetime import timedelta

def format_kmb(num):
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)

def format_count(num):
    if num is None: return "0"
    
    # 한국식 (만, 억)
    if num >= 100_000_000:
        return f"{num / 100_000_000:.1f}억"
    elif num >= 10_000:
        return f"{num / 10_000:.1f}만"
    
    # 1만 미만은 콤마(,)만 추가
    return f"{num:,}"

def render_video_player(info):
    st.subheader(f"📺 {info.title}")
    
    # 사용자가 제시한 iframe 방식 적용
    vid = info.video_id
    start = st.session_state.video_start_time
    autoplay = 1
    src = f"https://www.youtube.com/embed/{vid}?start={start}&autoplay={autoplay}&mute=1"

    st.components.v1.html(
        f"""
        <iframe
            width="100%"
            height="560"
            src="{src}"
            frameborder="0"
            allow="autoplay; encrypted-media; picture-in-picture"
            allowfullscreen
        ></iframe>
        """,
        height=580 
    )
    
    duration_str = str(timedelta(seconds=info.duration)) if info.duration else "알 수 없음"
    
    # 수치를 카드 형태로 나란히 배치
    m1, m2, m3 = st.columns(3)
    m2.metric("Views", format_kmb(info.viewCount))
    m3.metric("Likes", format_kmb(info.likeCount))
    with m1:
        st.markdown(f"👤 {info.channel_name}")
        st.markdown(f"⏱️ {duration_str}")

    # 태그는 아래에 작게
    if info.tags:
        st.caption(f"{' '.join(['#' + t for t in info.tags[:3]])}")
        
    # st.markdown(
    #     ":violet-badge[🐣 초급] :orange-badge[:material/star: 중급] :gray-badge[👿 고급]"
    
    # )
