"""
검색 키워드가 학습/교육 관련 내용인지 LLM을 통해 검증하는 모듈
"""

import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 학습 관련 키워드 판별 프롬프트
VALIDATION_PROMPT = """
Role: Learning/Education Classifier. 
Logic: Distinguish learning intent from pure entertainment/news.
[YES]: Tech/Coding, Academic(Math/Science/etc), Exams/Certs, Work Skills(Excel/Writing), Languages, Self-dev, Tutorials(Cooking/Music/Art).
[NO]: Gaming, Mukbang, Gossip, Ent, Music MV, Vlogs, News.
Output: JSON only. 
Format: {"is_learning": bool, "reason": "KR explanation, 1-2 sentences"}
"""


def validate_learning_keyword(query: str) -> dict:
    """
    검색 키워드가 학습/교육 관련인지 LLM으로 검증합니다.

    Args:
        query: 사용자 검색 키워드

    Returns:
        dict: {"is_learning": bool, "reason": str}
    """
    client = OpenAI()

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": VALIDATION_PROMPT.strip()},
                {"role": "user", "content": f"검색 키워드: {query}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,  # 일관된 판별을 위해 낮은 temperature
        )

        text = resp.choices[0].message.content.strip()
        result = json.loads(text)

        return {
            "is_learning": result.get("is_learning", False),
            "reason": result.get("reason", "판별 근거가 없습니다."),
        }

    except Exception as e:
        print(f"키워드 검증 중 오류 발생: {e}")
        # 검증 실패 시 기본적으로 통과 처리 (서비스 중단 방지)
        return {
            "is_learning": True,
            "reason": "검증 서비스 오류로 기본 허용 처리되었습니다.",
        }
