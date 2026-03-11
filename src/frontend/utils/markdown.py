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
