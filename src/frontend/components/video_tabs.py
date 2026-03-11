import streamlit as st
import requests
from config import API_URL
from utils.markdown import dict_to_markdown_quiz, dict_to_markdown_note
from utils.state_manager import set_video_time

def render_description_tab(info):
    data = info.parse_description()
    md_text = ""
    if data.get("summary"):
        md_text += f"### 강의 소개\n\n{data['summary']}\n\n"

    if data.get("timeline"):
        md_text += "### 강의 타임라인\n\n"
        for item in data["timeline"]:
            md_text += f"**{item['time']}** - {item['title']}\n\n"

    if data.get("links"):
        md_text += "### 관련 링크\n\n"
        for link in data["links"]:
            md_text += f"[{link}]({link})\n\n"

    if data.get("tags"):
        md_text += "### 태그\n\n"
        md_text += f"{' '.join(data['tags'])}\n\n"

    if data.get("cta"):
        md_text += f"{data['cta']}\n\n"

    st.markdown(
        f'<div class="scroll-box">\n\n{md_text}\n</div>', unsafe_allow_html=True
    )

def render_insight_tab(info):
    st.subheader("💡 AI 인사이트")
    cache_key = f"timeline_summary_{info.video_id}"

    if st.button(
        "AI 인사이트 및 타임라인 요약 생성하기",
        key=f"btn_create_summary_{info.video_id}",
    ):
        transcript_text = info.get_full_transcript()
        if transcript_text.strip():
            with st.spinner("🔍 AI 튜터가 영상을 분석 중입니다..."):
                res = requests.post(
                    f"{API_URL}/video/timeline-summary",
                    json={"transcript": transcript_text},
                )
                if res.status_code == 200:
                    st.session_state[cache_key] = res.json()
                    st.rerun()
                else:
                    st.error("요약을 생성하지 못했습니다.")
        else:
            st.warning("자막 데이터가 없어 요약할 수 없습니다.")

    if cache_key in st.session_state:
        summary_data = st.session_state[cache_key]
        md_text = summary_data.get("summary", "요약이 없습니다.")
        st.markdown(
            f'<div class="scroll-box">\n\n{md_text}\n\n</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info(
            "👆 위에 있는 재생성 버튼을 눌러 영상 내용을 한눈에 파악해 보세요."
        )

def render_timeline_tab(info):
    st.subheader("🕐 챕터별 타임라인")
    cache_key = f"timeline_summary_{info.video_id}"

    if cache_key in st.session_state:
        timeline_data = st.session_state[cache_key].get("timeline", [])
        with st.container(height=600):
            if timeline_data:
                for i, item in enumerate(timeline_data):
                    cols = st.columns([1, 4])
                    with cols[0]:
                        st.button(
                            f"▶ {item['start']}",
                            key=f"time_{info.video_id}_{i}",
                            on_click=set_video_time,
                            args=(item["start"],),
                            use_container_width=True,
                        )
                    with cols[1]:
                        st.markdown(f"**{item['title']}**")
            else:
                st.caption("타임라인 정보가 없습니다.\n\n")
    else:
        st.info("먼저 '인사이트' 탭에서 분석 버튼을 눌러주세요.")

def render_quiz_tab(info):
    st.subheader("✅ 퀴즈 및 도전과제")
    cache_key = f"quiz_{info.video_id}"

    if st.button("마크다운 생성하기", key=f"btn_create_quiz_{info.video_id}"):
        transcript_text = info.get_full_transcript()
        if transcript_text.strip():
            with st.spinner("🤖 AI 튜터가 퀴즈를 생성하고 있습니다..."):
                res = requests.post(
                    f"{API_URL}/video/quiz",
                    json={"transcript": transcript_text},
                )
                if res.status_code == 200:
                    st.session_state[cache_key] = res.json()
                else:
                    st.error("퀴즈 생성에 실패했습니다.")
        else:
            st.warning("자막 데이터가 없어 퀴즈를 생성할 수 없습니다.")

    if cache_key in st.session_state and st.session_state[cache_key]:
        md_text = dict_to_markdown_quiz(st.session_state[cache_key])
        st.download_button(
            label="📥 마크다운 다운로드",
            data=md_text,
            file_name=f"quiz_{info.video_id}.md",
            mime="text/markdown",
            key=f"btn_dl_quiz_{info.video_id}",
        )
        st.markdown(
            f'<div class="scroll-box">\n\n{md_text}\n</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info("버튼을 눌러 퀴즈를 생성해보세요.")

def render_note_tab(info):
    st.subheader("📚 학습 노트")
    cache_key = f"lecture_note_{info.video_id}"

    if st.button("마크다운 생성하기", key=f"btn_create_note_{info.video_id}"):
        transcript_text = info.get_full_transcript()
        if transcript_text.strip():
            with st.spinner("🤖 AI 튜터가 학습 노트를 생성하고 있습니다..."):
                res = requests.post(
                    f"{API_URL}/video/lecture-note",
                    json={"transcript": transcript_text},
                )
                if res.status_code == 200:
                    st.session_state[cache_key] = res.json()
                else:
                    st.error("학습 노트 생성에 실패했습니다.")
        else:
            st.warning("자막 데이터가 없어 학습 노트를 생성할 수 없습니다.")

    if cache_key in st.session_state and st.session_state[cache_key]:
        md_text = dict_to_markdown_note(st.session_state[cache_key])
        st.download_button(
            label="📥 마크다운 다운로드",
            data=md_text,
            file_name=f"lecture_note_{info.video_id}.md",
            mime="text/markdown",
            key=f"btn_dl_note_{info.video_id}",
        )
        st.markdown(
            f'<div class="scroll-box">\n\n{md_text}\n</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info("버튼을 눌러 학습 노트를 생성해보세요.")

def render_video_tabs(info):
    tab0, tab1, tab2, tab3, tab4 = st.tabs(
        ["설명", "인사이트", "타임라인", "퀴즈/과제", "학습노트"]
    )
    with tab0:
        render_description_tab(info)
    with tab1:
        render_insight_tab(info)
    with tab2:
        render_timeline_tab(info)
    with tab3:
        render_quiz_tab(info)
    with tab4:
        render_note_tab(info)
