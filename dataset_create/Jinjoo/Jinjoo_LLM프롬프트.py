# -*- coding: utf-8 -*-
import os
from openai import OpenAI

# ==============================================================================
# 1. 설정 영역 (Configuration)
# ==============================================================================

# OpenAI API 키 설정 (보안을 위해 환경 변수 사용을 권장)
# 터미널에서 'export OPENAI_API_KEY="YOUR_API_KEY"' 와 같이 설정
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


# ★★★ [사전 작업 필요] ★★★
# 아래 'STATIC_SYSTEM_PROMPT' 내용을 API로 한번 보내서 캐싱하고,
# 발급받은 ID를 여기에 붙여넣어. 이 작업은 딱 한 번만 하면 돼.
PROMPT_CACHE_ID = "여기에_캐싱해서_받은_ID를_붙여넣으세요"


# '고정부' 프롬프트: 이 내용은 바뀌지 않으므로 상수로 정의
STATIC_SYSTEM_PROMPT = """
# 역할
너는 1차 키워드 분석과 2차 맥락 분석 결과를 종합하여, 보이스피싱 위협으로부터 사용자를 보호하는 'AI 보안 전문가'야. 분석 내용을 바탕으로 사용자에게 명확하고 실행 가능한 경고를 제공해야 해.

# 지침
1.  주어진 `<model_1_output>`의 탐지 키워드와 `<model_2_output>`의 대화 맥락을 종합적으로 분석하여 보이스피싱 유형(예: 기관 사칭, 대출 사기)을 추론해.
2.  아래 `# 출력 형식`과 `# 예시`를 **반드시** 그대로 따라야 해.
3.  '핵심 경고 메시지'는 🚨 이모지로 시작하고, **"경고!"** 라는 단어를 포함하며, 2문장 이내로 명확하게 요약해야 해.
4.  '위험 이유'는 탐지된 키워드와 대화 맥락을 근거로 **왜** 위험한지 구체적으로 설명해야 해.
5.  '행동 요령'은 사용자가 **즉시** 실천할 수 있는 구체적인 행동 3가지를 번호 목록 형식으로 제시해야 해.
6.  지침과 형식 외에 다른 부가 설명이나 불필요한 말은 절대 덧붙이지 마.

# 출력 형식
- 핵심 경고 메시지: 
- 위험 이유: 
- 행동 요령:
  1. 
  2. 
  3. 

# 예시
<example>
  <model_1_output>
    탐지 키워드: "검찰", "계좌 이체", "사건 연루"
  </model_1_output>
  <model_2_output>
    대화 맥락 분석: 다급하고 위협적인 어조, 금전 이체 요구
  </model_2_output>
  <assistant_response>
- 핵심 경고 메시지: 🚨 경고! 정부기관을 사칭한 보이스피싱 전화일 확률이 매우 높습니다. 상대방의 요구에 절대 응하지 마세요.
- 위험 이유: '검찰', '사건 연루' 등의 단어를 사용하며 금전 이체를 요구하는 것은 전형적인 정부기관 사칭 사기 수법입니다. 정상적인 국가기관은 절대 전화로 자금 이체를 요구하지 않습니다.
- 행동 요령:
  1. 즉시 통화를 끊고 상대방 번호를 차단하세요.
  2. 돈을 이체하거나, 개인정보/금융정보를 절대 알려주지 마세요.
  3. 경찰(112) 또는 금융감독원(1332)에 직접 전화하여 사실 여부를 확인하세요.
  </assistant_response>
</example>
<example>
  <model_1_output>
    탐지 키워드: "저금리 대출", "신용등급", "수수료"
  </model_1_output>
  <model_2_output>
    대화 맥락 분석: 기존 대출 상환 유도, 선입금 요구
  </model_2_output>
  <assistant_response>
- 핵심 경고 메시지: 🚨 경고! 저금리 대출을 미끼로 한 금융사기일 가능성이 있습니다. 수수료나 선입금을 요구하면 100% 사기입니다.
- 위험 이유: '저금리 대출'을 명목으로 '수수료'나 기존 대출금 상환을 위한 선입금을 요구하는 것은 보이스피싱의 대표적인 유형입니다. 정상적인 금융기관은 대출을 이유로 선입금을 요구하지 않습니다.
- 행동 요령:
  1. 입금 요구에 절대 응하지 말고 즉시 통화를 종료하세요.
  2. '신용등급 상향' 등의 말에 현혹되지 마세요.
  3. 해당 금융사가 실제 존재하는지 금융소비자 정보포털 '파인' 등을 통해 확인하세요.
  </assistant_response>
</example>
"""


# ==============================================================================
# 2. 핵심 실행 함수 (Core Function)
# ==============================================================================


def generate_phishing_warning(keywords: list, context_analysis: str) -> str:
    """
    1, 2차 모델의 분석 결과를 받아 OpenAI API를 호출하고, 최종 경고 메시지를 반환한다.

    Args:
        keywords (list): 1차 모델이 탐지한 키워드 리스트
        context_analysis (str): 2차 모델의 맥락 분석 결과 문자열

    Returns:
        str: LLM이 생성한 최종 경고 메시지 또는 오류 메시지
    """
    if not PROMPT_CACHE_ID or "붙여넣으세요" in PROMPT_CACHE_ID:
        return (
            "오류: 프롬프트 캐시 ID가 설정되지 않았습니다. 스크립트 상단을 확인하세요."
        )

    # '가변부' 데이터를 동적으로 생성
    dynamic_user_message = f"""
<model_1_output>
  탐지 키워드: "{', '.join(keywords)}"
</model_1_output>
<model_2_output>
  대화 맥락 분석: "{context_analysis}"
</model_2_output>
"""

    try:
        # 캐시 ID와 가변부 데이터를 이용해 API 호출
        response = client.chat.completions.create(
            model="gpt-4o",
            prompt_id=PROMPT_CACHE_ID,
            messages=[{"role": "user", "content": dynamic_user_message}],
        )
        return response.choices[0].message.content

    except Exception as e:
        print(f"API 호출 중 오류가 발생했습니다: {e}")
        return "오류: 경고 메시지를 생성하는 데 실패했습니다."


# ==============================================================================
# 3. 실행 예시 (Example Usage)
# ==============================================================================

if __name__ == "__main__":
    # --- 시나리오 1: 기관 사칭 ---
    print("--- [시나리오 1: 기관 사칭] 경고 메시지 생성 ---")
    detected_keywords_1 = ["서울중앙지검", "계좌 동결", "범죄 연루"]
    detected_context_1 = "다급하고 권위적인 어조로 현금 이체를 강하게 요구함"
    final_warning_1 = generate_phishing_warning(detected_keywords_1, detected_context_1)
    print(final_warning_1)
    print("\n" + "=" * 50 + "\n")

    # --- 시나리오 2: 대출 사기 ---
    print("--- [시나리오 2: 대출 사기] 경고 메시지 생성 ---")
    detected_keywords_2 = ["햇살론", "대환대출", "보증료", "선입금"]
    detected_context_2 = (
        "기존 대출을 먼저 갚아야 저금리 대출이 가능하다며 특정 계좌로 입금을 유도함"
    )
    final_warning_2 = generate_phishing_warning(detected_keywords_2, detected_context_2)
    print(final_warning_2)
