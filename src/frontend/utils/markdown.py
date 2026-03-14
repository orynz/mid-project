import re
import streamlit as st
from utils.state_manager import set_video_time


def convert_timestamps_to_links(text: str, key_prefix: str = "ts"):
    """
    [MM:SS] 또는 [HH:MM:SS] 형식의 타임스탬프를 Streamlit 버튼으로 변환하여 렌더링합니다.
    [time] **title** 형식이면 버튼 라벨에 제목을 포함합니다.
    """
    # 타임스탬프와 뒤따르는 선택적 제목 패턴 (**제목**)
    pattern = r"\[(\d{1,2}(?::\d{1,2})?:\d{2})\](?:\s*\*\*(.*?)\*\*)?"

    # 텍스트를 패턴 기준으로 분할 (그룹 1: 시간, 그룹 2: 제목)
    parts = re.split(pattern, text)

    # re.split에 2개의 괄호 그룹이 있으므로, 각 매칭마다 [텍스트, 그룹1, 그룹2] 순으로 요소가 들어감
    # 따라서 i=0(텍스트), i+1(시간), i+2(제목) 순서로 접근
    for i in range(0, len(parts), 3):
        # 1. 일반 텍스트 부분 출력
        if i < len(parts) and parts[i] and parts[i].strip():
            st.markdown(parts[i])

        # 2. 타임스탬프 버튼 부분 출력
        if i + 1 < len(parts):
            time_str = parts[i + 1]
            title_str = parts[i + 2] if i + 2 < len(parts) and parts[i + 2] else None

            # 버튼 라벨 구성: f"▶ [{time_str}] | {title}"
            label = f"▶ [{time_str}]"
            if title_str:
                label += f" | {title_str.strip()}"

            st.button(
                label,
                key=f"btn_{key_prefix}_{time_str}_{i}",
                type="tertiary",
                on_click=set_video_time,
                args=(time_str,),
            )


def dict_to_markdown_quiz(data: dict) -> str:
    if "error" in data:
        return data["error"]
    md = "#### 📝 퀴즈 및 도전과제\n\n"
    if "questions" in data:
        for i, q in enumerate(data.get("questions", []), 1):
            md += f"###### Q{i}. {q.get('question', '')}\n\n"
            for j, opt in enumerate(q.get("options", []), 1):
                md += f"{j}. {opt}\n"
            md += f"\n**정답 및 해설:**\n{q.get('answer', '')}\n\n---\n\n"

    if "challenge" in data:
        md += "#### 🚀 도전 과제\n\n"
        for i, c in enumerate(data.get("challenge", []), 1):
            md += f"###### Challenge {i}\n\n**문제:**\n{c.get('question', '')}\n\n**예시 답안:**\n{c.get('answer', '')}\n\n"
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
