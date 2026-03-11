from typing import Literal
import time

template = """
Role: Strict 1:1 IT AI Tutor
Task: Gen IT/Prog test based on [Input].
Lang: Korean
Out: FINAL QUIZ ONLY.

Args:
- Diff: {difficulty} (Low: MCQ/blank | Mid: apply | High: eval/optimize)
- N: {num_questions}
- Date: {current_date}

Flow (Silent):
1. Topic: Extract core IT/Prog concept.
2. Draft: N Qs matching Diff. If Chal: +1 Code/Algo Q.
3. Verify: Concepts from [Material] BUT universally solvable via general IT knowledge (Strictly NO material-specific trivia).
4. Rule for Chal: MUST provide explicit sample datasets/conditions in "question" (NO vague references). "answer" MUST be a complete functioning code block.

JSON Output Schema:
{{
  "metadata": {{
    "created_at": "{current_date}",
    "difficulty": "{difficulty}"
  }},
  "questions": [
    {{
      "question": "Detailed question (use \n for line breaks)",
      "options": ["Opt1", "Opt2", "Opt3", "Opt4"],
      "answer": "Exact answer and detailed reasoning based on lecture"
    }}
  ]
  "challenge": [
      {{
          "question": "Code/Algo Q. Include CONCRETE input/output data & strict conditions (use \n for line breaks and Markdown)",
          "answer": "Complete code block solution (use \n for line breaks and Markdown)"
      }}
  ]
}}

[Input]: {lecture_content}
"""

def generate_prompt(
    lecture_content:str,
    difficulty: Literal["Low","Mid","High"]="Mid",
    num_questions:int=3,
) -> str:
    """퀴즈 생성 프롬프트

    Args:
        lecture_content (str): 자막(스크립트)
        difficulty ("Low","Mid","High", optional): 난이도. Defaults to "Low".
        num_questions (int, optional): 문항수. Defaults to 3.
        include_challenge (bool, optional): 도전문제. Defaults to False.

    Returns:
        str: 프롬프트
    """
    
    current_date = time.strftime("%Y-%m-%d %H:%M:%S")

    prompt = template.format(
        difficulty=difficulty,
        num_questions=num_questions,
        current_date=current_date,
        lecture_content=lecture_content
    )
    
    return prompt
