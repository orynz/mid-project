template = """
# Role: Elite Edu-Designer & Tech Summarizer
# Task: Process `{transcript_data}` (auto-correct STT typos contextually) into an entity-dense KR global summary & chapters.

# Rules
1. CoD Summary: Extract overarching core insights (NOT timeline-based). ≤{max_words} words. Iterate {iterations} times, adding {entity_range} tech entities/step. Fuse ALL entities. Cut fillers. Use KR Markdown. 내용 중 특정 시점을 언급할 때는 반드시 [MM:SS] 또는 [HH:MM:SS] 형식을 사용하세요.
2. Timeline: 4-8 concept-based chapters. Start: "MM:SS". Title: "1. KR_Title".
3. Output: STRICT minified JSON ONLY. Zero meta-text.

{{"summary":"<use \n for line breaks>","timeline":[{{"start":"MM:SS","title":"1. KR_Title"}}]}}
"""

def generate_prompt(transcript_data:str, max_words:int=200, entity_range="3~5", iterations:int=3) -> str:
    """챕터 분할을 위한 프롬프트 반환

    Args:
        transcript_data (str): 타임라인 기반 자막(스크립트) 데이터

    Returns:
        str: 프롬프트 리턴
    """
    return template.format(
        transcript_data = transcript_data,
        max_words = max_words,
        entity_range = entity_range,
        iterations = iterations
    )