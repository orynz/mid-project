import streamlit as st
import requests
from config import API_URL
from utils.markdown import dict_to_markdown_quiz, dict_to_markdown_note, convert_timestamps_to_links
from utils.state_manager import set_video_time

def render_description_tab(info):
    data = info.parse_description()
    md_text = ""
    if data.get("summary"):
        md_text += f"### 강의 소개\n\n{data['summary']}\n\n"

    # if data.get("timeline"):
    #     md_text += "### 강의 타임라인\n\n"
    #     for item in data["timeline"]:
    #         # 대괄호를 추가하여 convert_timestamps_to_links가 인식할 수 있게 함
    #         md_text += f"[{item['time']}] **{item['title']}**"

    if data.get("links"):
        md_text += "### 관련 링크\n\n"
        for link in data["links"]:
            md_text += f"[{link}]({link})\n\n"

    if data.get("tags"):
        md_text += "### 태그\n\n"
        md_text += f"{' '.join(data['tags'])}\n\n"

    if data.get("cta"):
        md_text += f"{data['cta']}\n\n"

    with st.container(height=600):
        convert_timestamps_to_links(md_text, key_prefix="desc")

def render_insight_tab(info):
    cache_key = f"timeline_summary_{info.video_id}"
    if st.button(
        "AI 분석 요약 생성/갱신",
        key=f"btn_create_summary_{info.video_id}",
        width="stretch"
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
        with st.container(height=600):
            convert_timestamps_to_links(md_text, key_prefix="summary")
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
                    cols = st.columns([1, 5], vertical_alignment="center")
                    with cols[0]:
                        st.button(
                            f"▶ {item['start']}",
                            key=f"time_{info.video_id}_{i}",
                            on_click=set_video_time,
                            args=(item["start"],),
                            width="stretch",
                            type="primary",
                        )
                    with cols[1]:
                        # st.markdown(f"##### {item['title']}")
                        st.write(item['title'])
            else:
                st.caption("타임라인 정보가 없습니다.\n\n")
    else:
        st.info("먼저 '인사이트' 탭에서 분석 버튼을 눌러주세요.")

def render_quiz_tab(info):
    cache_key = f"quiz_{info.video_id}"

    if cache_key in st.session_state and st.session_state[cache_key]:
        md_text = dict_to_markdown_quiz(st.session_state[cache_key])
        cols = st.columns([1,1])
        with cols[0]:
            if st.button("다시 생성하기", key=f"btn_create_quiz_{info.video_id}", width="stretch"):
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
        with cols[1]:
            st.download_button(
                label="📥 다운로드",
                data=md_text,
                file_name=f"quiz_{info.video_id}.md",
                mime="text/markdown",
                key=f"btn_dl_quiz_{info.video_id}",
                width="stretch",
                type="primary"
            )
            
        st.markdown(
            f'<div class="scroll-box">\n\n{md_text}\n</div>',
            unsafe_allow_html=True,
        )
    else:
        if st.button("퀴즈 생성하기", key=f"btn_create_quiz_{info.video_id}", width="stretch"):
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
                
        st.info("버튼을 눌러 퀴즈를 생성해보세요.")

def render_note_tab(info):
    cache_key = f"lecture_note_{info.video_id}"

    if cache_key in st.session_state and st.session_state[cache_key]:
        md_text = dict_to_markdown_note(st.session_state[cache_key])
        
        cols = st.columns([1,1])
        with cols[0]:
            if st.button("다시 생성하기", key=f"btn_create_note_{info.video_id}", width="stretch"):
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
        with cols[1]:
            st.download_button(
                label="📥 다운로드",
                data=md_text,
                file_name=f"lecture_note_{info.video_id}.md",
                mime="text/markdown",
                key=f"btn_dl_note_{info.video_id}",
                width="stretch",
                type="primary"
            )
            
        st.markdown(
            f'<div class="scroll-box">\n\n{md_text}\n</div>',
            unsafe_allow_html=True,
        )
    else:
        if st.button("노트 생성하기", key=f"btn_create_note_{info.video_id}", width="stretch"):
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
            
        st.info("버튼을 눌러 학습 노트를 생성해보세요.")

def render_rag_tab(info):
    st.markdown("### 🤖 대화형 AI 튜터")
    st.markdown("강의 내용에 대해 궁금한 점을 물어보세요. 관련 타임라인과 함께 답변해 드립니다.")
    
    chat_key = f"rag_messages_{info.video_id}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []
    
    # 채팅 기록 표시 영역 (스크롤 박스 형태)
    chat_container = st.container(height=500)
    with chat_container:
        for i, msg in enumerate(st.session_state[chat_key]):
            role_class = "user-message" if msg["role"] == "user" else "assistant-message"
            name = "👤 나" if msg["role"] == "user" else "🤖 AI 튜터"
            
            # 메시지 컨테이너
            with st.container():
                st.markdown(f"**{name}**")
                if msg["role"] == "assistant":
                    # AI 답변은 타임스탬프 버튼 포함 가능
                    convert_timestamps_to_links(msg["content"], key_prefix=f"chat_{i}")
                else:
                    st.markdown(msg["content"])
                st.divider()
    
    # 채팅 입력
    if prompt := st.chat_input("질문을 입력하세요", key=f"chat_input_{info.video_id}"):
        # 사용자 메시지 저장 및 즉시 표시
        st.session_state[chat_key].append({"role": "user", "content": prompt})
        
        # AI 응답 생성
        try:
            payload = {
                "video_id": info.video_id,
                "question": prompt,
                "video_url": info.url
            }
            with st.spinner("AI가 답변을 준비 중입니다..."):
                response = requests.post(f"{API_URL}/video/rag", json=payload)
                if response.status_code == 200:
                    rag_data = response.json()
                    answer = rag_data.get('answer', '답변을 생성하지 못했습니다.')
                    # 답변을 미리 가공하지 않고 원문 그대로 저장 (렌더링 시점에 변환)
                    st.session_state[chat_key].append({"role": "assistant", "content": answer})
                else:
                    st.error("답변 생성 중 오류가 발생했습니다.")
            st.rerun()
        except Exception as e:
            st.error(f"연결 오류: {e}")

def render_transcript_tab(info):
    st.subheader("📜 전체 자막")
    transcript = info.get_full_transcript()
    if transcript.strip():
        # 대괄호 추가하여 링크 변환
        processed_transcript = ""
        for line in transcript.split("\n"):
            if line.strip():
                # "00:00) text" -> "[00:00] text"
                if ")" in line:
                    time_part, text_part = line.split(")", 1)
                    processed_transcript += f"[{time_part}] {text_part}\n\n"
                # else: 
                #     processed_transcript += f"{line}\n\n"
        
        with st.container(height=600):
            convert_timestamps_to_links(processed_transcript, key_prefix="transcript")
    else:
        st.warning("자막 데이터가 없습니다.")

def render_video_tabs(info):
    tabs = st.tabs(
        ["📝 설명", "💡 AI 인사이트", "🕐 챕터", "🤖 튜터", "✅ 퀴즈", "📚 학습노트", "📜 자막"]
    )
    
    with tabs[0]:
        render_description_tab(info)

    with tabs[1]:
        render_insight_tab(info)
        
    with tabs[2]:
        render_timeline_tab(info)

    with tabs[3]:
        render_rag_tab(info)

    with tabs[4]:
        render_quiz_tab(info)

    with tabs[5]:
        render_note_tab(info)

    with tabs[6]:
        render_transcript_tab(info)
