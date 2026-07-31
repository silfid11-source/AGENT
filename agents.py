from agent_rules import SHOWPARK_AGENT_RULES
from reference_analyzer import load_reference_rules


def ask_agent(client, model_name, agent_name, prompt):
    reference_rules = load_reference_rules()
    reference_block = ""
    if reference_rules:
        reference_block = f"""
[레퍼런스 분석 규칙]
아래 규칙은 사용자가 넣어둔 레퍼런스 예시를 분석해서 만든 스타일 기준이야.
가능한 한 이 규칙을 우선 적용해.

{reference_rules}
"""

    response = client.responses.create(
        model=model_name,
        input=f"""
너는 ShowPark AI Studio의 {agent_name}야.
모든 답변은 한국어로 작성해.
바로 실무에 사용할 수 있게 구체적으로 작성해.

{SHOWPARK_AGENT_RULES}

{reference_block}

{prompt}
""",
    )
    return response.output_text


def run_showpark_agent_pipeline(client, model_name, context):
    common_context = f"""
[프로젝트 정보]
- 콘텐츠 목적: {context["content_goal"]}
- 주제: {context["topic_text"]}
- 고객명/브랜드명: {context["brand_display"]}
- 지역: {context["region_display"]}
- 업종: {context["industry_name"]}
- 타깃: {context["target"]}
- 고객의 현실 문제: {context["pain"]}
- 업종 시각 요소: {context["visual"]}
- 기본 톤: {context["tone"]}
- 콘텐츠 스타일: {context["content_style"]}
- 프롬프트 프리셋: {context["prompt_preset"]}
- 창의성 모드: {context["creativity_mode"]}
- 영상 길이: {context["video_length"]}
- 게시 플랫폼: {context["platform"]}
"""

    strategy_result = ask_agent(
        client,
        model_name,
        "기획 전략 에이전트",
        f"""
{common_context}

[역할]
콘텐츠의 전체 방향을 먼저 설계해.

[출력]
# 1. 콘텐츠 방향 요약
- 어떤 사장님을 겨냥하는지
- 어떤 감정을 건드리는지
- 어떤 행동을 유도하는지
- 전체 메시지 한 줄
""",
    )

    copy_result = ask_agent(
        client,
        model_name,
        "카피라이팅 에이전트",
        f"""
{common_context}

[기획 결과]
{strategy_result}

[역할]
썸네일, 릴스 대본, 캡션, 해시태그를 만든다.

[출력]
# 2. 썸네일 문구 10개

# 3. 릴스 3문장 대본 5개

# 4. 인스타 캡션 3개

# 5. 해시태그 20개
""",
    )

    image_result = ask_agent(
        client,
        model_name,
        "이미지 프롬프트 에이전트",
        f"""
{common_context}

[기획 결과]
{strategy_result}

[역할]
같은 주제라도 매번 다른 이미지가 나오도록 창의적인 이미지 프롬프트를 만든다.

[출력]
# 6. 이미지 생성 프롬프트
조건:
- 서로 다른 이미지 프롬프트 변형안 3개
- 각 변형안은 구도, 조명, 소품, 분위기, 카메라 시점이 다를 것
- 9:16 세로 이미지
- 얼굴 노출 없음
- 업종을 일반화하지 말 것
- 각 변형안마다 한국어 프롬프트와 영어 프롬프트 작성
- 마지막에 공통으로 피해야 할 표현 작성
""",
    )

    video_result = ask_agent(
        client,
        model_name,
        "영상 프롬프트 에이전트",
        f"""
{common_context}

[기획 결과]
{strategy_result}

[역할]
영상 생성툴에 바로 넣을 수 있는 영상 프롬프트와 장면표를 만든다.

[출력]
# 7. 영상 생성 프롬프트

# 8. 장면 구성표
| 시간 | 장면 | 화면 설명 | 자막 |
| 0~2초 |  |  |  |
| 2~5초 |  |  |  |
| 5초 이후 |  |  |  |
""",
    )

    production_result = ask_agent(
        client,
        model_name,
        "제작 검수 에이전트",
        f"""
{common_context}

[기획 결과]
{strategy_result}

[카피 결과]
{copy_result}

[이미지 프롬프트]
{image_result}

[영상 프롬프트]
{video_result}

[역할]
게시 전 자막 문구와 제작 주의사항을 정리하고, 전체 결과의 약점을 짧게 점검한다.

[출력]
# 9. 추천 자막 문구 10개

# 10. 제작 시 주의사항
- 피해야 할 표현
- 피해야 할 장면
- 더 자연스럽게 보이게 하는 팁

# 에이전트 검수 메모
- 좋은 점 3개
- 보완한 점 3개
""",
    )

    final_result = ask_agent(
        client,
        model_name,
        "최종 조립 에이전트",
        f"""
아래 분야별 에이전트 결과를 하나의 최종 콘텐츠 패키지로 정리해.

[중요]
- 반드시 # 1부터 # 10까지 순서대로 출력할 것
- 중복 문장은 줄일 것
- 에이전트 검수 메모는 마지막에 짧게 남길 것
- 업종 "{context["industry_name"]}"을 절대 일반화하지 말 것
- 바로 복사해서 사용할 수 있는 최종본만 출력할 것

[기획 에이전트]
{strategy_result}

[카피 에이전트]
{copy_result}

[이미지 에이전트]
{image_result}

[영상 에이전트]
{video_result}

[검수 에이전트]
{production_result}
""",
    )

    agent_report = "\n\n".join(
        [
            "# 분야별 에이전트 작업 기록",
            "## 1. 기획 전략 에이전트",
            strategy_result,
            "## 2. 카피라이팅 에이전트",
            copy_result,
            "## 3. 이미지 프롬프트 에이전트",
            image_result,
            "## 4. 영상 프롬프트 에이전트",
            video_result,
            "## 5. 제작 검수 에이전트",
            production_result,
        ]
    )

    return {
        "result": final_result,
        "agent_report": agent_report,
    }
