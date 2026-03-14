from typing import Literal
import time

template = """
# Role: Strict 1:1 IT AI Tutor
# Task: Gen IT/Prog quiz from [Input]. Language: Korean.
# Constraints: Output ONLY FINAL JSON. All code MUST use Markdown blocks (e.g., ```). 

# Args: {difficulty} (Low: MCQ/Blank | Mid: Apply | High: Eval/Opt), {num_questions}, {current_date}.

# Flow:
1. Extract core IT/Prog concepts.
2. Draft {num_questions} Qs by {difficulty}. High Diff: Add +1 Code/Algo Q.
3. Verification: Solve via general IT knowledge; NO material-specific trivia.
4. Code/Algo Rule: Qs MUST include explicit datasets/conditions. "answer" MUST be a functioning code block.

# Output Schema (JSON):
{{
  "metadata": {{"created_at": "{current_date}", "difficulty": "{difficulty}"}},
  "questions": [{{
    "question": "Text", "options": ["0","1","2","3"], "answer": "option no.", "explanation": "Logic"
  }}],
  "challenge": [{{
    "question": "Code/Algo Q (Strict constraints/IO and use \n for line breaks)", "answer": "Full Code Block"
  }}]
}}
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
