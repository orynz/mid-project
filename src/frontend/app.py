import asyncio, httpx, requests
from typing import List, Optional
from backend.shared.youtube_schema import YouTubeInfo, ChapterItem, SubtitleItem
import streamlit as st
from datetime import timedelta

API_URL = "http://localhost:8000"


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
    height: 600px;          /* 원하는 높이 */
    overflow-y: auto;       /* 세로 스크롤 */
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 10px;
}
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------
# 상태 초기화 및 콜백 함수
# -----------------------------
if "selected_video" not in st.session_state:  # 영상 ID 세션
    st.session_state.selected_video = YouTubeInfo
if "recommended_videos" not in st.session_state:  # 추천 영상 데이터
    st.session_state.recommended_videos = [YouTubeInfo]
if "video_start_time" not in st.session_state:
    st.session_state.video_start_time = 0


def dict_to_markdown_quiz(data: dict) -> str:
    if "error" in data:
        return data["error"]
    md = "### 📝 퀴즈 및 도전과제\n\n"
    if "questions" in data:
        for i, q in enumerate(data.get("questions", []), 1):
            md += f"#### Q{i}. {q.get('question', '')}\n\n"
            for j, opt in enumerate(q.get("options", []), 1):
                md += f"{j}. {opt}\n"
            md += f"\n**정답 및 해설:**\n{q.get('answer', '')}\n\n---\n\n"

    if "challenge" in data:
        md += "### 🚀 도전 과제\n\n"
        for i, c in enumerate(data.get("challenge", []), 1):
            md += f"#### Challenge {i}\n\n**문제:**\n{c.get('question', '')}\n\n**예시 답안:**\n{c.get('answer', '')}\n\n"
    return md


def dict_to_markdown_note(data: dict) -> str:
    if "error" in data:
        return data["error"]

    md = "### 📚 학습 노트\n\n"

    overview = data.get("lecture_overview", {})
    if overview:
        md += f"#### 1. 개요\n- **주제:** {overview.get('topic', '')}\n"
        md += f"- **난이도:** {overview.get('difficulty_level', '')}\n"
        md += f"- **선수 지식:** {', '.join(overview.get('prerequisites', []))}\n\n"

    if data.get("learning_objectives"):
        md += "#### 2. 학습 목표\n"
        for obj in data.get("learning_objectives", []):
            md += f"- {obj}\n"
        md += "\n"

    if data.get("key_terms"):
        md += "#### 3. 핵심 용어\n"
        for term in data.get("key_terms", []):
            md += f"- **{term.get('term', '')}**: {term.get('definition', '')}\n"
        md += "\n"

    if data.get("core_content"):
        md += "#### 4. 핵심 내용\n"
        for idx, content in enumerate(data.get("core_content", []), 1):
            md += f"##### 4.{idx} {content.get('section_title', '')}\n\n"
            md += f"{content.get('concept_explanation', '')}\n\n"
            if content.get("visual_summary"):
                md += f"{content.get('visual_summary')}\n\n"

            for code in content.get("code_examples", []):
                md += f"**[코드 예시: {code.get('title', '')}]**\n```\n{code.get('code', '')}\n```\n"
                md += f"- 설명: {code.get('line_by_line_explanation', '')}\n"
                md += f"- 출력: {code.get('expected_output', '')}\n\n"

            if content.get("common_mistakes"):
                md += "**⚠️ 흔한 실수:**\n"
                for mistake in content.get("common_mistakes", []):
                    md += f"- {mistake}\n"
                md += "\n"

            if content.get("deep_dive"):
                md += f"{content.get('deep_dive')}\n\n"

            if content.get("real_world_usage"):
                md += f"**💡 실무 활용:** {content.get('real_world_usage')}\n\n"

    if data.get("hands_on_practice"):
        md += "#### 5. 실습 문제\n"
        for practice in data.get("hands_on_practice", []):
            md += f"##### {practice.get('exercise_title', '')} (난이도: {practice.get('difficulty', '')})\n"
            md += f"**문제:** {practice.get('problem', '')}\n\n"
            if practice.get("hint"):
                md += f"**힌트:** {practice.get('hint', '')}\n\n"
            md += f"**정답:**\n```\n{practice.get('solution', '')}\n```\n"
            md += f"**해설:** {practice.get('solution_explanation', '')}\n\n"

    if data.get("core_faq"):
        md += "#### 6. 자주 묻는 질문 (FAQ)\n"
        for faq in data.get("core_faq", []):
            md += f"- **Q.** {faq.get('question', '')}\n"
            md += f"  **A.** {faq.get('answer', '')}\n\n"

    if data.get("further_study"):
        md += "#### 7. 추가 학습 자료\n"
        for study in data.get("further_study", []):
            md += f"- {study}\n"

    return md


def change_video(selected_video):
    """추천 영상 카드를 클릭했을 때 즉시 상태를 업데이트하는 콜백 함수"""
    st.session_state.selected_video = selected_video
    st.session_state.video_start_time = 0


def set_video_time(time_str):
    """타임라인 클릭 시 영상 시작 시간을 변경하는 콜백 함수"""
    try:
        parts = time_str.split(":")
        if len(parts) == 2:
            seconds = int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        else:
            seconds = 0
        st.session_state.video_start_time = seconds
    except:
        st.session_state.video_start_time = 0


def get_insite_info():
    info = st.session_state.selected_video
    return {"message": "ok"}

    res = requests.post(f"{API_URL}/video/summarize/{info.get_full_transcript()}")

    if res.status_code == 200:
        data = res.json()
        return data
    else:
        st.error(f"오류: {res.text}")
        return {"message": res.text}


# -------------------------
# 사이드바 메뉴
# -------------------------
with st.sidebar:
    st.markdown("#### 💬 채팅 기록")
    st.caption("기록이 없습니다.")
    st.markdown("---")


# -------------------------
# 상단 입려창
# -------------------------
def trigger_search():
    if st.session_state.top_search_input:
        st.session_state.pending_search = st.session_state.top_search_input


st.title("👾 AI 학습 큐레이터")
st.text_input(
    "배우고 싶은 내용을 알려주세요",
    label_visibility="hidden",
    placeholder="예: 파이썬 기초 영상 추천해줘",
    key="top_search_input",
    on_change=trigger_search,
)
# List[YouTubeInfo]
user_input = st.session_state.get("pending_search", "")
if user_input:
    st.session_state.pending_search = ""
    with st.spinner("🔍 AI 튜터가 영상을 검색하고 분석하는 중입니다..."):
        res = requests.post(f"{API_URL}/video/search/{user_input}")

        if res.status_code == 200:
            data = res.json()
            video_list = [YouTubeInfo.model_validate(item) for item in data]
            st.session_state.recommended_videos = video_list
            print(video_list)
            change_video(video_list[0])
            st.rerun()
        elif res.status_code == 400:
            error_data = res.json()
            st.warning(
                f"🚫 학습과 관련 없는 키워드입니다: {error_data.get('detail', '다시 시도해 주세요.')}"
            )
        else:
            st.error(f"오류: {res.text}")

st.divider()

# -------------------------
# 좌측 영역 (메인 영상)
# -------------------------
left_col, right_col = st.columns([1, 1])

if isinstance(st.session_state.selected_video, YouTubeInfo):
    with left_col:
        info = st.session_state.selected_video
        st.subheader("📺 메인 영상")
        st.video(info.url, start_time=st.session_state.video_start_time)
        st.markdown(
            f"""
                    #### 📘 {info.title}

                    ##### 영상길이: {str(timedelta(seconds=info.duration))}
                    ###### 채널명: {info.channel_name}
                    """
        )
        st.markdown(
            ":violet-badge[🐣 초급] :orange-badge[:material/star: 중급] :gray-badge[👿 고급]"
        )

    # -------------------------
    # 우측 영역 (탭)
    # -------------------------
    with right_col:
        tab0, tab1, tab2, tab3, tab4 = st.tabs(
            ["설명", "인사이트", "타임라인", "퀴즈/과제", "학습노트"]
        )
        with tab0:
            data = info.parse_description()

            md_text = ""
            if data["summary"]:
                md_text += f"### 강의 소개\n\n{data['summary']}\n\n"

            if data["timeline"]:
                md_text += "### 강의 타임라인\n\n"
                for item in data["timeline"]:
                    md_text += f"**{item['time']}** - {item['title']}\n\n"

            if data["links"]:
                md_text += "### 관련 링크\n\n"
                for link in data["links"]:
                    md_text += f"[{link}]({link})\n\n"

            if data["tags"]:
                md_text += "### 태그\n\n"
                md_text += f"{' '.join(data['tags'])}\n\n"

            if data["cta"]:
                md_text += f"{data['cta']}\n\n"

            st.markdown(
                f'<div class="scroll-box">\n\n{md_text}\n</div>', unsafe_allow_html=True
            )

        with tab1:
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

        with tab2:
            st.subheader("🕐 챕터별 타임라인")
            cache_key = f"timeline_summary_{info.video_id}"

            if cache_key in st.session_state:
                timeline_data = st.session_state[cache_key].get("timeline", [])
                # <div> 태그 내 위젯 배치가 불가능하므로, 기본 지원하는 컨테이너 사용
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
        with tab3:
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

        with tab4:
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

    # -------------------------
    # 하단 영역 (영상 추천)
    # -------------------------
    st.divider()
    st.subheader("🔎 추천 영상")

    cols = st.columns(3)

    # 컨테이너와 버튼을 사용한 카드형 UI 렌더링
    for i, info in enumerate(st.session_state.recommended_videos):
        with cols[i]:
            # 현재 선택된 영상인지 판별
            is_selected = st.session_state.selected_video.video_id == info.video_id

            # 추천 영상 카드
            with st.container(border=True):
                st.image(
                    f"https://img.youtube.com/vi/{info.video_id}/0.jpg", width="stretch"
                )

                # 제목 (적당한 길이 유지)
                display_title = (
                    info.title if len(info.title) <= 45 else info.title[:43] + "..."
                )
                st.markdown(f"**{display_title}**")

                # 채널명 및 영상 길이
                duration_str = (
                    str(timedelta(seconds=info.duration))
                    if info.duration
                    else "알 수 없음"
                )
                st.caption(f"👤 **{info.channel_name}** | ⏱️ {duration_str}")

                # 태그 최대 5개
                if info.tags:
                    tags_html = " ".join([f"`#{tag}`" for tag in info.tags[:5]])
                    st.markdown(tags_html)
                else:
                    st.markdown("Unknown") # 줄 맞춤용 공백

                # 선택 효과: 선택된 영상은 눈에 띄는 색상(primary)으로 변경 및 텍스트 변경
                button_type = "primary" if is_selected else "secondary"
                button_label = "✅ 선택 영상" if is_selected else "▶️ 재생하기"

                # st.rerun() 대신 콜백(on_click)을 사용하여 속도와 정확도 향상
                st.button(
                    button_label,
                    key=f"btn_{info.video_id}",
                    type=button_type,
                    use_container_width=True,
                    on_click=change_video,
                    args=(info,),
                )
