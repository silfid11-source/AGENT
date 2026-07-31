import os
import re
import random
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from agents import run_showpark_agent_pipeline


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("OPENAI_API_KEY를 .env 파일에서 찾을 수 없습니다.")
    st.stop()

client = OpenAI(api_key=api_key)

st.set_page_config(
    page_title="ShowPark AI Studio",
    page_icon="🎬",
    layout="centered",
)

st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0f1117 !important;
        color: #ffffff !important;
        color-scheme: dark;
    }

    .main {
        background-color: #0f1117 !important;
    }

    header, [data-testid="stToolbar"], #MainMenu {
        visibility: hidden;
        height: 0;
    }

    h1 {
        font-size: 42px !important;
        font-weight: 800 !important;
        color: #ffffff !important;
    }

    h2, h3, label, p {
        color: #ffffff !important;
    }

    .stTextInput input {
        border-radius: 10px;
        padding: 12px;
    }

    .stSelectbox div {
        border-radius: 10px;
    }

    .stButton button {
        width: 100%;
        border-radius: 10px;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        color: white;
        font-weight: 700;
        padding: 12px;
        border: none;
    }

    .stButton button:hover {
        background: linear-gradient(90deg, #2563eb, #7c3aed);
        color: white;
    }

    .stDownloadButton button {
        width: 100%;
        border-radius: 10px;
        background-color: #1f2937;
        color: white;
        font-weight: 700;
        padding: 12px;
        border: 1px solid #374151;
    }

    .block-container {
        padding-top: 3rem;
        max-width: 850px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("# 🎬 ShowPark AI Studio")
st.markdown(
    "### 주제 하나로 릴스 대본, 이미지 프롬프트, 영상 프롬프트, 캡션, 해시태그까지 한 번에 생성합니다."
)
st.caption("개인용 숏폼 콘텐츠 제작 AI 스튜디오")

today_key = datetime.now().strftime("%Y-%m-%d")

if st.session_state.get("usage_date") != today_key:
    st.session_state.usage_date = today_key
    st.session_state.generate_count = 0
    st.session_state.improve_count = 0

usage_placeholder = st.empty()

with usage_placeholder.container():
    usage_col1, usage_col2 = st.columns(2)
    usage_col1.metric("오늘 생성 횟수", f"{st.session_state.generate_count}회")
    usage_col2.metric("오늘 다듬기 횟수", f"{st.session_state.improve_count}회")

industries = {
    "식당": {
        "target": "30~40대 식당 사장님",
        "tone": "현실적이고 직설적인 톤",
        "pain": "음식은 괜찮지만 온라인에서 매장의 차별점이 잘 보이지 않는 상황",
    },
    "카페": {
        "target": "동네 카페 사장님",
        "tone": "감성적이지만 설득력 있는 톤",
        "pain": "공간은 예쁘지만 온라인 노출과 방문 전환이 약한 상황",
    },
    "병원": {
        "target": "병원 원장님 또는 마케팅 담당자",
        "tone": "신뢰감 있고 전문적인 톤",
        "pain": "광고비는 쓰고 있지만 신뢰를 만드는 콘텐츠가 부족한 상황",
    },
    "미용실": {
        "target": "미용실 원장님",
        "tone": "트렌디하고 시각적인 톤",
        "pain": "실력은 좋지만 신규 고객이 결과물을 쉽게 확인하기 어려운 상황",
    },
    "헬스장": {
        "target": "헬스장 대표님",
        "tone": "활기차고 결과 중심적인 톤",
        "pain": "시설은 좋은데 상담 전환이 약한 상황",
    },
    "부동산": {
        "target": "부동산 대표님",
        "tone": "신뢰감 있고 현실적인 톤",
        "pain": "좋은 매물은 있지만 온라인에서 눈에 띄지 않는 상황",
    },
    "학원": {
        "target": "학원 원장님",
        "tone": "전문적이고 학부모 친화적인 톤",
        "pain": "수업 퀄리티는 좋지만 신규 상담 문의가 꾸준하지 않은 상황",
    },
    "네일샵": {
        "target": "네일샵 원장님",
        "tone": "감각적이고 트렌디한 톤",
        "pain": "결과물은 예쁘지만 신규 고객에게 충분히 도달하지 못하는 상황",
    },
    "피부관리실": {
        "target": "피부관리실 원장님",
        "tone": "고급스럽고 신뢰감 있는 톤",
        "pain": "효과를 설명해야 하지만 광고처럼 보이면 신뢰가 떨어지는 상황",
    },
    "필라테스": {
        "target": "필라테스 센터 대표님",
        "tone": "건강하고 세련된 톤",
        "pain": "수업 퀄리티는 높지만 체험 문의가 약한 상황",
    },
    "펜션": {
        "target": "펜션 또는 숙박업 운영자",
        "tone": "감성적이고 여행 욕구를 자극하는 톤",
        "pain": "공간은 좋지만 노출이 예약으로 이어지지 않는 상황",
    },
    "꽃집": {
        "target": "꽃집 사장님",
        "tone": "따뜻하고 감성적인 톤",
        "pain": "상품은 예쁘지만 온라인에서 오래 기억되기 어려운 상황",
    },
    "세차장": {
        "target": "세차장 또는 디테일링샵 대표님",
        "tone": "깔끔하고 결과 중심적인 톤",
        "pain": "전후 차이는 강하지만 영상으로 잘 보여주지 못하는 상황",
    },
    "PT샵": {
        "target": "PT샵 대표님",
        "tone": "동기부여가 되고 결과 중심적인 톤",
        "pain": "운동 효과는 분명하지만 상담 전환이 약한 상황",
    },
    "온라인 쇼핑몰": {
        "target": "온라인 쇼핑몰 운영자",
        "tone": "구매 욕구를 자극하지만 과장 없는 톤",
        "pain": "상품은 좋지만 상세페이지와 광고만으로 신뢰를 만들기 어려운 상황",
    },
    "라멘집": {
        "target": "라멘집 사장님",
        "tone": "좁지만 활기 있고 먹음직스러운 톤",
        "pain": "맛과 분위기는 확실하지만 온라인에서 라멘집 특유의 매력이 충분히 전달되지 않는 상황",
        "visual": "김이 나는 라멘 그릇, 차슈, 면, 라멘 바 좌석, 일본식 주방, 따뜻한 조명",
    },
    "치킨집": {
        "target": "치킨집 사장님",
        "tone": "친근하고 식욕을 자극하는 톤",
        "pain": "튀김과 메뉴의 매력은 강하지만 온라인에서 차별점이 비슷해 보이는 상황",
        "visual": "바삭한 치킨 클로즈업, 치킨 무, 포장 박스, 배달 봉투, 튀김 소리, 가족형 매장",
    },
    "한의원": {
        "target": "한의원 원장님 또는 실장님",
        "tone": "차분하고 신뢰감 있는 톤",
        "pain": "전문성과 편안함을 보여줘야 하지만 병원 광고처럼 보이면 신뢰가 떨어지는 상황",
        "visual": "한약재, 맥진, 침구실, 한방차, 차분한 상담 공간, 따뜻한 원목 분위기",
    },
    "치과": {
        "target": "치과 원장님 또는 상담 실장님",
        "tone": "깔끔하고 안심되는 톤",
        "pain": "전문성은 있지만 고객이 느끼는 두려움과 부담을 콘텐츠로 풀기 어려운 상황",
        "visual": "깨끗한 진료실, 상담 데스크, 치아 모형, 밝은 조명, 위생적인 장비",
    },
    "베이커리": {
        "target": "베이커리 사장님",
        "tone": "따뜻하고 먹음직스러운 톤",
        "pain": "빵과 공간은 매력적이지만 매일 방문할 이유가 온라인에서 약한 상황",
        "visual": "갓 구운 빵, 진열대, 크루아상, 밀가루 질감, 오븐, 따뜻한 아침 조명",
    },
    "와인바": {
        "target": "와인바 대표님",
        "tone": "고급스럽고 분위기 있는 톤",
        "pain": "분위기는 좋지만 처음 오는 고객에게 진입 장벽이 있어 보이는 상황",
        "visual": "와인잔, 낮은 조명, 바 테이블, 치즈 플레이트, 병 진열장, 어두운 우드톤",
    },
    "곱창집": {
        "target": "곱창집 사장님",
        "tone": "식욕을 강하게 자극하는 현실적인 톤",
        "pain": "맛과 현장감은 강하지만 영상으로 생생하게 보여주지 못하는 상황",
        "visual": "철판 위 곱창, 불판 연기, 기름진 윤기, 부추, 소스, 시끌벅적한 저녁 분위기",
    },
    "사진관": {
        "target": "사진관 대표님",
        "tone": "감성적이고 신뢰감 있는 톤",
        "pain": "촬영 결과물은 좋지만 고객이 예약 전에 분위기를 상상하기 어려운 상황",
        "visual": "촬영 조명, 카메라, 배경지, 액자, 앨범, 자연스러운 스튜디오 분위기",
    },
    "웨딩스튜디오": {
        "target": "웨딩스튜디오 대표님",
        "tone": "고급스럽고 설레는 톤",
        "pain": "결과물은 아름답지만 비슷한 웨딩 콘텐츠 사이에서 차별점이 약한 상황",
        "visual": "웨딩드레스 디테일, 부케, 베일, 스튜디오 조명, 고급 액자, 부드러운 색감",
    },
    "애견미용": {
        "target": "애견미용샵 원장님",
        "tone": "따뜻하고 믿음직한 톤",
        "pain": "실력과 케어는 좋지만 보호자가 안심할 수 있는 장면이 부족한 상황",
        "visual": "미용 테이블, 빗, 가위, 목욕 거품, 깔끔한 털 정리, 편안한 반려견 공간",
    },
    "키즈카페": {
        "target": "키즈카페 운영자",
        "tone": "밝고 안전감 있는 톤",
        "pain": "시설은 좋지만 부모가 안심하고 방문할 이유를 콘텐츠로 보여주기 어려운 상황",
        "visual": "놀이시설, 안전매트, 밝은 색감, 정리된 공간, 부모 대기석, 아이 눈높이 소품",
    },
    "인테리어": {
        "target": "인테리어 업체 대표님",
        "tone": "전문적이고 결과 중심적인 톤",
        "pain": "시공 퀄리티는 좋지만 전후 차이와 신뢰 요소가 콘텐츠에서 약한 상황",
        "visual": "시공 전후, 자재 샘플, 도면, 공구, 조명, 깔끔한 완성 공간",
    },
}


def ask_ai(prompt, model_name):
    response = client.responses.create(
        model=model_name,
        input=prompt,
    )
    return response.output_text
def improve_result(original_result, improve_type, model_name):
    prompt = f"""
너는 숏폼 콘텐츠 제작 대행사 'ShowPark'의 콘텐츠 디렉터야.

아래 기존 결과물을 "{improve_type}" 방향으로 다시 다듬어줘.

[수정 원칙]
- 모든 답변은 한국어로 작성할 것
- 기존 업종, 지역, 브랜드명, 주제의 맥락은 유지할 것
- 결과물의 구조는 최대한 유지할 것
- 너무 광고처럼 보이지 않게 할 것
- 바로 복사해서 사용할 수 있게 정리할 것

[기존 결과물]
{original_result}
"""

    response = client.responses.create(
        model=model_name,
        input=prompt,
    )
    return response.output_text


def check_content_quality(content, industry_name, region, topic_text, model_name):
    prompt = f"""
너는 숏폼 콘텐츠 제작 대행사 'ShowPark'의 품질 검수자야.

아래 콘텐츠가 실제 릴스 제작과 게시에 바로 쓸 수 있는지 검사해줘.

[검사 기준]
- 업종 "{industry_name}"이 일반적인 표현으로 뭉개지지 않았는지
- 지역 "{region if region else "미입력"}"이 억지스럽지 않게 반영됐는지
- 주제 "{topic_text}"와 결과물이 잘 맞는지
- 썸네일, 대본, 캡션, 해시태그, 이미지 프롬프트, 영상 프롬프트가 서로 같은 방향을 보고 있는지
- 너무 광고처럼 보이는 표현이 있는지
- 얼굴 노출 없이 제작 가능한지
- 이미지/영상 프롬프트가 실제 생성툴에 넣기 충분히 구체적인지
- 바로 게시하기 전에 고치면 좋은 부분이 있는지

[출력 형식]
# 품질 검사 결과

## 총점
- 100점 만점으로 점수와 짧은 이유

## 좋은 점
- 3개

## 수정이 필요한 점
- 3개

## 바로 고치면 좋아지는 문장
- 원문:
- 수정:

## 게시 전 체크리스트
- 체크박스 형식으로 5개

[검사할 콘텐츠]
{content}
"""

    response = client.responses.create(
        model=model_name,
        input=prompt,
    )
    return response.output_text


def agent_finalize_result(original_result, quality_report, model_name):
    prompt = f"""
너는 숏폼 콘텐츠 제작 대행사 'ShowPark'의 자동 개선 에이전트야.

아래 품질 검사 결과를 반영해서 기존 콘텐츠 패키지를 최종본으로 다시 정리해줘.

[작업 목표]
- 품질 검사에서 지적된 약점을 실제 결과물에 반영할 것
- 기존 업종, 지역, 브랜드명, 주제는 유지할 것
- 결과물의 10개 섹션 구조를 유지할 것
- 이미지 프롬프트와 영상 프롬프트는 더 창의적이고 구체적으로 만들 것
- 썸네일, 릴스 대본, 캡션, 해시태그가 같은 메시지로 연결되게 만들 것
- 바로 복사해서 쓸 수 있게 최종본만 출력할 것

[유지할 출력 구조]
# 1. 콘텐츠 방향 요약
# 2. 썸네일 문구 10개
# 3. 릴스 3문장 대본 5개
# 4. 인스타 캡션 3개
# 5. 해시태그 20개
# 6. 이미지 생성 프롬프트
# 7. 영상 생성 프롬프트
# 8. 장면 구성표
# 9. 추천 자막 문구 10개
# 10. 제작 시 주의사항

[품질 검사 결과]
{quality_report}

[기존 콘텐츠]
{original_result}
"""

    response = client.responses.create(
        model=model_name,
        input=prompt,
    )
    return response.output_text


def regenerate_content_direction(original_result, current_direction, model_name):
    direction_focus = random.choice(
        [
            "더 선명한 고객 타깃",
            "더 강한 문제 제기",
            "더 자연스러운 문의 전환",
            "더 고급스러운 브랜드 신뢰",
            "더 현실적인 사장님 공감",
            "더 메뉴나 상품 매력 중심",
            "더 지역 고객 관점",
            "더 저장하고 싶은 정보형 방향",
            "더 조회수 후킹 중심",
            "더 단골 재방문 유도 중심",
        ]
    )
    direction_seed = random.randint(1000, 9999)

    prompt = f"""
너는 숏폼 콘텐츠 전략가야.

아래 기존 콘텐츠의 업종, 지역, 브랜드, 주제 맥락은 유지하되,
콘텐츠 방향 요약만 완전히 새롭게 다시 작성해줘.

[이번 새 방향]
{direction_focus}

[반복 방지 번호]
{direction_seed}

[수정 원칙]
- 반드시 '# 1. 콘텐츠 방향 요약' 제목으로 시작할 것.
- 기존 방향 요약과 같은 표현, 같은 논리를 반복하지 말 것.
- 어떤 사장님을 겨냥하는지 작성할 것.
- 어떤 감정을 건드리는지 작성할 것.
- 어떤 행동을 유도하는지 작성할 것.
- 이후 대본, 캡션, 이미지/영상 프롬프트가 따라가기 쉬운 방향으로 정리할 것.

[기존 전체 콘텐츠]
{original_result}

[기존 콘텐츠 방향]
{current_direction}
"""

    response = client.responses.create(
        model=model_name,
        input=prompt,
    )
    return response.output_text


def regenerate_caption(original_result, current_caption, model_name):
    caption_direction = random.choice(
        [
            "첫 줄 후킹을 더 강하게",
            "문의 전환을 더 자연스럽게",
            "브랜드 신뢰감을 더 높이게",
            "사장님 고민에 더 공감하게",
            "고객이 저장하고 싶게",
            "방문 욕구를 더 자극하게",
            "더 짧고 읽기 쉽게",
            "더 고급스럽고 차분하게",
            "더 직설적이고 명확하게",
            "댓글 반응을 유도하게",
        ]
    )
    caption_seed = random.randint(1000, 9999)

    prompt = f"""
너는 인스타그램 캡션 카피라이터야.

아래 기존 콘텐츠의 업종, 지역, 브랜드, 주제 맥락은 유지하되,
인스타 캡션만 완전히 새롭게 다시 작성해줘.

[이번 새 방향]
{caption_direction}

[반복 방지 번호]
{caption_seed}

[수정 원칙]
- 반드시 '# 4. 인스타 캡션 3개' 제목으로 시작할 것.
- 기존 캡션과 같은 첫 줄, 같은 문장 구조, 같은 마무리를 반복하지 말 것.
- 캡션은 3개 작성할 것.
- 각 캡션은 첫 줄 후킹, 짧은 본문, 자연스러운 행동 유도로 구성할 것.
- 너무 광고처럼 보이지 않게 작성할 것.
- 바로 복사해서 인스타에 붙여넣을 수 있게 작성할 것.

[기존 전체 콘텐츠]
{original_result}

[기존 캡션]
{current_caption}
"""

    response = client.responses.create(
        model=model_name,
        input=prompt,
    )
    return response.output_text


def regenerate_hashtags(original_result, current_hashtags, model_name):
    hashtag_direction = random.choice(
        [
            "지역 노출을 더 강화",
            "업종 전문성을 더 강화",
            "릴스 탐색 노출을 더 고려",
            "잠재 고객 검색어를 더 반영",
            "너무 넓은 태그를 줄이고 구체화",
            "브랜드 감도를 더 고급스럽게",
            "자영업자 타깃을 더 선명하게",
            "방문과 문의 전환을 더 고려",
            "소형 계정도 노출될 만한 태그 조합",
            "플랫폼 알고리즘에 자연스러운 조합",
        ]
    )
    hashtag_seed = random.randint(1000, 9999)

    prompt = f"""
너는 숏폼 콘텐츠 해시태그 전략가야.

아래 기존 콘텐츠의 업종, 지역, 브랜드, 주제 맥락은 유지하되,
해시태그만 완전히 새롭게 다시 작성해줘.

[이번 새 방향]
{hashtag_direction}

[반복 방지 번호]
{hashtag_seed}

[수정 원칙]
- 반드시 '# 5. 해시태그 20개' 제목으로 시작할 것.
- 기존 해시태그와 같은 조합을 반복하지 말 것.
- 해시태그는 정확히 20개 작성할 것.
- 너무 넓은 해시태그만 반복하지 말 것.
- 업종, 지역, 콘텐츠 주제, 릴스 노출, 잠재 고객 검색어를 섞을 것.
- 실제 게시물에 바로 붙여넣을 수 있게 한 줄 또는 보기 쉬운 묶음으로 작성할 것.

[기존 전체 콘텐츠]
{original_result}

[기존 해시태그]
{current_hashtags}
"""

    response = client.responses.create(
        model=model_name,
        input=prompt,
    )
    return response.output_text


def regenerate_subtitle_lines(original_result, current_subtitle_lines, model_name):
    subtitle_direction = random.choice(
        [
            "더 짧고 강한 자막",
            "첫 1초에 멈춰보게 하는 자막",
            "사장님 현실에 더 꽂히는 자막",
            "고객이 공감하기 쉬운 자막",
            "문의 행동을 자연스럽게 유도하는 자막",
            "저장하고 싶게 만드는 정보형 자막",
            "더 고급스럽고 차분한 자막",
            "더 직설적이고 날카로운 자막",
            "화면 전환에 맞는 리듬감 있는 자막",
            "댓글 반응을 유도하는 자막",
        ]
    )
    subtitle_seed = random.randint(1000, 9999)

    prompt = f"""
너는 숏폼 영상 자막 카피라이터야.

아래 기존 콘텐츠의 업종, 지역, 브랜드, 주제 맥락은 유지하되,
추천 자막 문구만 완전히 새롭게 다시 작성해줘.

[이번 새 방향]
{subtitle_direction}

[반복 방지 번호]
{subtitle_seed}

[수정 원칙]
- 반드시 '# 9. 추천 자막 문구 10개' 제목으로 시작할 것.
- 기존 자막과 같은 표현, 같은 문장 구조를 반복하지 말 것.
- 자막 문구는 10개 작성할 것.
- 각 자막은 화면에 바로 올릴 수 있게 짧게 작성할 것.
- 너무 길면 모바일 화면에서 읽기 어려우므로 1줄 중심으로 작성할 것.
- 업종, 콘텐츠 목적, 지역 맥락을 자연스럽게 반영할 것.
- 얼굴 노출 없는 영상에도 잘 어울리는 자막으로 작성할 것.

[기존 전체 콘텐츠]
{original_result}

[기존 자막 문구]
{current_subtitle_lines}
"""

    response = client.responses.create(
        model=model_name,
        input=prompt,
    )
    return response.output_text


def regenerate_production_notes(original_result, current_notes, model_name):
    note_direction = random.choice(
        [
            "촬영자가 바로 이해하기 쉽게",
            "피해야 할 장면을 더 구체적으로",
            "광고 티를 줄이는 방향으로",
            "브랜드 고급감을 지키는 방향으로",
            "얼굴 노출 없는 촬영 팁 중심으로",
            "영상 생성 AI에서 깨지기 쉬운 요소 중심으로",
            "현장 촬영과 AI 생성 둘 다 고려",
            "소품과 배경 실수를 줄이는 방향으로",
            "자막과 화면 충돌을 피하는 방향으로",
            "더 자연스러운 숏폼 완성도 중심으로",
        ]
    )
    note_seed = random.randint(1000, 9999)

    prompt = f"""
너는 숏폼 콘텐츠 제작 감독이야.

아래 기존 콘텐츠의 업종, 지역, 브랜드, 주제 맥락은 유지하되,
제작 시 주의사항만 완전히 새롭게 다시 작성해줘.

[이번 새 방향]
{note_direction}

[반복 방지 번호]
{note_seed}

[수정 원칙]
- 반드시 '# 10. 제작 시 주의사항' 제목으로 시작할 것.
- 피해야 할 표현, 피해야 할 장면, 더 자연스럽게 보이게 하는 팁을 포함할 것.
- 기존 주의사항과 같은 표현을 반복하지 말 것.
- 이미지 생성, 영상 생성, 실제 편집 과정에서 조심할 점을 구체적으로 작성할 것.
- 얼굴 노출 없는 콘텐츠 기준으로 작성할 것.
- 바로 제작 체크리스트처럼 쓸 수 있게 짧고 명확하게 작성할 것.

[기존 전체 콘텐츠]
{original_result}

[기존 제작 시 주의사항]
{current_notes}
"""

    response = client.responses.create(
        model=model_name,
        input=prompt,
    )
    return response.output_text


def regenerate_thumbnail_hooks(original_result, current_thumbnail_hooks, model_name):
    hook_direction = random.choice(
        [
            "더 강한 위기감",
            "더 궁금하게 만드는 질문형",
            "더 직설적인 경고형",
            "더 저장하고 싶은 정보형",
            "더 고급스럽고 신뢰감 있는 표현",
            "더 지역 고객이 멈춰볼 표현",
            "더 자영업자 현실에 꽂히는 표현",
            "더 메뉴나 상품 매력이 보이는 표현",
            "더 짧고 자극적인 6~8자 문구",
            "더 부드럽지만 설득력 있는 표현",
        ]
    )
    hook_seed = random.randint(1000, 9999)

    prompt = f"""
너는 숏폼 썸네일 후킹 카피라이터야.

아래 기존 콘텐츠의 업종, 지역, 브랜드, 주제 맥락은 유지하되,
썸네일 문구만 완전히 새롭게 다시 작성해줘.

[이번 새 방향]
{hook_direction}

[반복 방지 번호]
{hook_seed}

[수정 원칙]
- 반드시 '# 2. 썸네일 문구 10개' 제목으로 시작할 것.
- 기존 썸네일 문구와 같은 단어, 같은 문장 구조를 반복하지 말 것.
- 썸네일 문구는 10개 작성할 것.
- 각 문구는 10자 내외로 짧고 강하게 작성할 것.
- 업종 사장님이 멈춰볼 만한 현실적인 문구로 작성할 것.
- 너무 싸구려 광고처럼 보이지 않게 작성할 것.
- 바로 이미지나 영상 썸네일에 얹을 수 있게 작성할 것.

[기존 전체 콘텐츠]
{original_result}

[기존 썸네일 문구]
{current_thumbnail_hooks}
"""

    response = client.responses.create(
        model=model_name,
        input=prompt,
    )
    return response.output_text


def regenerate_reels_script(original_result, current_reels_script, model_name):
    script_direction = random.choice(
        [
            "첫 문장을 더 자극적으로",
            "사장님 공감을 더 강하게",
            "문의 전환을 더 자연스럽게",
            "더 짧고 빠른 리듬으로",
            "더 현실적인 문제 제기로",
            "더 고급스럽고 신뢰감 있게",
            "더 저장하고 싶은 정보형으로",
            "더 댓글을 유도하는 방식으로",
            "더 지역 고객이 공감하게",
            "더 메뉴나 상품 매력이 보이게",
        ]
    )
    script_seed = random.randint(1000, 9999)

    prompt = f"""
너는 숏폼 릴스 대본 디렉터야.

아래 기존 콘텐츠의 업종, 지역, 브랜드, 주제 맥락은 유지하되,
릴스 3문장 대본만 완전히 새롭게 다시 작성해줘.

[이번 새 방향]
{script_direction}

[반복 방지 번호]
{script_seed}

[수정 원칙]
- 반드시 '# 3. 릴스 3문장 대본 5개' 제목으로 시작할 것.
- 기존 대본과 같은 첫 문장, 같은 흐름, 같은 표현을 반복하지 말 것.
- 대본은 5개 작성할 것.
- 각 대본은 3문장으로 작성할 것.
- 1문장: 후킹.
- 2문장: 현실 문제 또는 욕구.
- 3문장: 캡션 확인, 문의, 예약, 방문 중 자연스러운 행동 유도.
- 얼굴 노출 없는 나레이션 형식으로 작성할 것.
- 말하듯이 짧고 강하게 작성할 것.

[기존 전체 콘텐츠]
{original_result}

[기존 릴스 대본]
{current_reels_script}
"""

    response = client.responses.create(
        model=model_name,
        input=prompt,
    )
    return response.output_text


def regenerate_image_prompt(original_result, current_image_prompt, creativity_mode, model_name):
    creative_direction = random.choice(
        [
            "전혀 다른 카메라 각도",
            "새로운 조명 분위기",
            "다른 계절감과 시간대",
            "다른 소품과 배경 구성",
            "더 시네마틱한 클로즈업",
            "더 현실적인 매장 스냅샷",
            "더 고급스러운 광고 화보 느낌",
            "손님 시점에서 보는 장면",
            "제품과 공간을 동시에 보여주는 구도",
            "작은 디테일로 업종 정체성을 보여주는 장면",
        ]
    )
    creative_seed = random.randint(1000, 9999)

    prompt = f"""
너는 AI 이미지 프롬프트 디렉터야.

아래 기존 콘텐츠의 업종, 지역, 브랜드, 주제 맥락은 유지하되,
이미지 생성 프롬프트만 완전히 새롭게 다시 작성해줘.

[현재 창의성 모드]
{creativity_mode}

[이번 새 방향]
{creative_direction}

[반복 방지 번호]
{creative_seed}

[수정 원칙]
- 반드시 '# 6. 이미지 생성 프롬프트' 제목으로 시작할 것.
- 기존 이미지 프롬프트와 같은 구도, 같은 소품, 같은 문장 구조를 반복하지 말 것.
- 서로 다른 이미지 프롬프트 변형안 3개를 작성할 것.
- 각 변형안은 구도, 조명, 카메라 시점, 소품, 분위기 중 최소 3개가 서로 다르게 보이게 작성할 것.
- 얼굴 노출 없음.
- 9:16 세로 이미지 기준.
- 입력 업종을 일반화하지 말고 원래 업종명을 유지할 것.
- 각 변형안마다 한국어 프롬프트와 영어 프롬프트를 함께 작성할 것.
- 마지막에 공통으로 피해야 할 표현을 작성할 것.

[기존 전체 콘텐츠]
{original_result}

[기존 이미지 프롬프트]
{current_image_prompt}
"""

    response = client.responses.create(
        model=model_name,
        input=prompt,
    )
    return response.output_text


def regenerate_video_prompt(original_result, current_video_prompt, creativity_mode, model_name):
    creative_direction = random.choice(
        [
            "첫 1초 후킹을 더 강하게",
            "카메라 이동을 더 역동적으로",
            "장면 전환을 더 빠르게",
            "공간 분위기를 더 시네마틱하게",
            "제품 클로즈업을 더 선명하게",
            "문제 상황과 해결 장면을 더 분명하게",
            "자막과 화면 흐름을 더 직관적으로",
            "손님 시점의 발견 장면으로 구성",
            "브랜드 고급감을 더 살리는 연출",
            "현실적인 숏폼 광고 촬영 느낌",
        ]
    )
    creative_seed = random.randint(1000, 9999)

    prompt = f"""
너는 AI 영상 프롬프트 디렉터야.

아래 기존 콘텐츠의 업종, 지역, 브랜드, 주제 맥락은 유지하되,
영상 생성 프롬프트와 장면 구성표만 완전히 새롭게 다시 작성해줘.

[현재 창의성 모드]
{creativity_mode}

[이번 새 방향]
{creative_direction}

[반복 방지 번호]
{creative_seed}

[수정 원칙]
- 반드시 '# 7. 영상 생성 프롬프트'와 '# 8. 장면 구성표' 두 제목을 모두 포함할 것.
- 기존 영상 프롬프트와 같은 카메라 움직임, 같은 장면 순서, 같은 자막 흐름을 반복하지 말 것.
- 9:16 세로 영상 기준.
- 얼굴 노출 없음.
- 입력 업종을 일반화하지 말고 원래 업종명을 유지할 것.
- 카메라 움직임, 장면 순서, 자막 흐름을 구체적으로 작성할 것.
- 한국어 프롬프트와 영어 프롬프트를 함께 작성할 것.
- 장면 구성표는 시간, 장면, 화면 설명, 자막으로 정리할 것.

[기존 전체 콘텐츠]
{original_result}

[기존 영상 프롬프트와 장면 구성표]
{current_video_prompt}
"""

    response = client.responses.create(
        model=model_name,
        input=prompt,
    )
    return response.output_text


def clean_filename(text):
    text = text.strip()
    text = text.replace(" ", "")
    text = text.replace("/", "_")
    text = text.replace("\\", "_")
    text = text.replace(":", "_")
    text = text.replace("*", "_")
    text = text.replace("?", "_")
    text = text.replace('"', "_")
    text = text.replace("<", "_")
    text = text.replace(">", "_")
    text = text.replace("|", "_")

    if len(text) > 20:
        text = text[:20]

    return text if text else "미입력"


def split_result_sections(content):
    matches = list(re.finditer(r"(?m)^#\s*(\d+)\.\s*.+$", content))
    sections = {}

    for index, match in enumerate(matches):
        section_number = int(match.group(1))
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        sections[section_number] = content[start:end].strip()

    return sections


def get_sections_text(sections, section_numbers):
    parts = [
        sections[number]
        for number in section_numbers
        if number in sections and sections[number].strip()
    ]

    return "\n\n".join(parts).strip()


def replace_result_section(content, section_number, new_section):
    pattern = re.compile(r"(?m)^#\s*(\d+)\.")
    matches = list(pattern.finditer(content))

    for index, match in enumerate(matches):
        if int(match.group(1)) != section_number:
            continue

        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        return f"{content[:start].rstrip()}\n\n{new_section.strip()}\n\n{content[end:].lstrip()}".strip()

    return f"{content.rstrip()}\n\n{new_section.strip()}".strip()


def replace_result_section_range(content, start_section, end_section, new_section):
    pattern = re.compile(r"(?m)^#\s*(\d+)\.")
    matches = list(pattern.finditer(content))
    start = None
    end = None

    for index, match in enumerate(matches):
        section_number = int(match.group(1))

        if section_number == start_section:
            start = match.start()

        if section_number == end_section:
            end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
            break

    if start is None:
        return f"{content.rstrip()}\n\n{new_section.strip()}".strip()

    if end is None:
        end = len(content)

    return f"{content[:start].rstrip()}\n\n{new_section.strip()}\n\n{content[end:].lstrip()}".strip()


def section_download_button(label, content, filename_prefix, key):
    if not content.strip():
        return

    file_name = f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    st.download_button(
        label=label,
        data=content,
        file_name=file_name,
        mime="text/plain",
        key=key,
    )


def save_result(content, industry_name, region, topic_text):

    project_name = f"{industry_name}_{region}"

    project_name = (
        project_name
        .replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
    )

    project_folder = os.path.join(
        "projects",
        project_name
    )

    os.makedirs(project_folder, exist_ok=True)

    now = datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = os.path.join(
        project_folder,
        f"{topic_text}_{now}.txt"
    )

    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)

    return filename
def split_and_save_result(content, project_folder):
    os.makedirs(project_folder, exist_ok=True)

    sections = {
    "01_콘텐츠_방향.txt": "# 1. 콘텐츠 방향 요약",
    "02_썸네일_후킹.txt": "# 2. 썸네일 문구 10개",
    "03_릴스_대본.txt": "# 3. 릴스 3문장 대본 5개",
    "04_인스타_캡션.txt": "# 4. 인스타 캡션",
    "05_해시태그.txt": "# 5. 해시태그",
    "06_이미지_프롬프트.txt": "# 6. 이미지 생성 프롬프트",
    "07_영상_프롬프트.txt": "# 7. 영상 생성 프롬프트",
    "08_장면_구성표.txt": "# 8. 장면 구성표",
    "09_자막_문구.txt": "# 9. 추천 자막 문구",
    "10_제작_노트.txt": "# 10. 제작 시 주의사항",
}

    saved_files = []

    for filename, marker in sections.items():

        start = content.find(marker)

        if start == -1:
            continue

        next_positions = []

        for next_marker in sections.values():
            pos = content.find(next_marker, start + 1)

            if pos != -1:
                next_positions.append(pos)

        end = min(next_positions) if next_positions else len(content)

        section_content = content[start:end].strip()

        file_path = os.path.join(
            project_folder,
            filename
        )

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(section_content)

        saved_files.append(file_path)

    return saved_files
def custom_industry_profile(industry_name):
    return {
        "target": f"{industry_name} 운영자 또는 대표님",
        "tone": "현실적이고 구체적이며 설득력 있는 톤",
        "pain": f"{industry_name}만의 장점은 있지만 온라인 콘텐츠에서 그 매력이 구체적으로 보이지 않는 상황",
        "visual": f"{industry_name} 특유의 공간, 상품, 도구, 소품, 조명, 고객이 실제로 보는 장면",
    }


st.caption("필요한 정보를 빠르게 입력하세요.")

input_col1, input_col2 = st.columns(2)

with input_col1:
    content_goal = st.selectbox(
        "콘텐츠 목적",
        [
            "신규 고객 유입",
            "문의/예약 전환",
            "브랜드 신뢰도 상승",
            "메뉴/상품 홍보",
            "이벤트/할인 홍보",
            "단골 고객 재방문 유도",
        ],
    )

with input_col2:
    topic = st.text_input(
        "콘텐츠 주제",
        placeholder="예: 인스타 안 하는 매장이 손해보는 이유",
    )

input_col3, input_col4 = st.columns(2)

with input_col3:
    brand_name = st.text_input(
        "고객명 또는 브랜드명",
        placeholder="예: 멘야쇼파크, 강남 PT샵, 홍대 곱창집",
    )

with input_col4:
    region = st.text_input(
        "지역",
        placeholder="예: 홍대, 강남, 성수, 부산 서면, 대구 동성로",
    )

input_col5, input_col6 = st.columns(2)

with input_col5:
    industry_choice = st.selectbox(
        "업종 선택",
        list(industries.keys()) + ["직접 입력"],
    )

custom_industry = ""
if industry_choice == "직접 입력":
    with input_col6:
        custom_industry = st.text_input(
            "직접 입력 업종",
            placeholder="예: 라멘집, 치킨집, 한의원, 애견미용, 와인바",
        )
else:
    with input_col6:
        st.caption("목록에서 업종을 선택했습니다.")

setting_col1, setting_col2 = st.columns(2)

with setting_col1:
    video_length = st.selectbox(
        "영상 길이",
        ["5초", "10초", "15초"],
        key="video_length_setting",
    )

with setting_col2:
    content_style = st.selectbox(
        "콘텐츠 스타일",
        ["직설형", "신뢰형", "감성형", "고급형", "자극형"],
    )

setting_col3, setting_col4 = st.columns(2)

with setting_col3:
    prompt_preset = st.selectbox(
        "프롬프트 프리셋",
        [
            "기본형",
            "고객 설득형",
            "조회수 후킹형",
            "브랜드 고급형",
            "자영업자 공감형",
            "전환 집중형",
        ],
    )

with setting_col4:
    creativity_mode = st.selectbox(
        "창의성 모드",
        [
            "안정형",
            "균형형",
            "창의형",
            "실험형",
        ],
    )

setting_col7, setting_col8 = st.columns(2)

with setting_col7:
    output_type = st.selectbox(
        "생성할 결과 유형",
        [
            "전체 패키지",
            "릴스 대본만",
            "이미지 프롬프트만",
            "영상 프롬프트만",
            "인스타 캡션만",
            "해시태그만",
        ],
    )

with setting_col8:
    platform = st.selectbox(
        "게시 플랫폼",
        [
            "인스타 릴스",
            "유튜브 쇼츠",
            "틱톡",
            "공통 숏폼",
        ],
    )

setting_col9, setting_col10 = st.columns(2)

with setting_col9:
    model_mode = st.selectbox(
        "AI 모델 선택",
        ["저비용 모드", "일반 모드", "고품질 모드"],
    )

model_descriptions = {
    "저비용 모드": "테스트용으로 적합합니다. 비용을 아끼면서 초안을 확인할 때 사용하세요.",
    "일반 모드": "실사용 기본 모드입니다. 품질과 비용의 균형이 좋습니다.",
    "고품질 모드": "최종 납품용 결과를 만들 때 사용하세요. API 사용량이 더 커질 수 있습니다.",
}

st.caption(model_descriptions[model_mode])

st.caption("콘텐츠 생성 또는 결과 다듬기 버튼을 누르면 OpenAI API 사용량이 발생합니다.")

high_quality_confirmed = True

if model_mode == "고품질 모드":
    high_quality_confirmed = st.checkbox(
        "고품질 모드는 비용이 더 들 수 있음을 확인했습니다.",
        key="high_quality_confirmed",
    )

model_map = {
    "저비용 모드": "gpt-5-nano",
    "일반 모드": "gpt-5-mini",
    "고품질 모드": "gpt-5",
}

selected_model = model_map[model_mode]

action_col1, action_col2 = st.columns(2)
with action_col1:
    generate = st.button("콘텐츠 패키지 생성")
with action_col2:
    agent_generate = st.button("분야별 에이전트 실행")

st.caption("분야별 에이전트 실행은 기획, 카피, 이미지, 영상, 검수 에이전트를 순서대로 호출하므로 API 사용량이 더 발생합니다.")

if "result" not in st.session_state:
    st.session_state.result = ""

if "industry_name" not in st.session_state:
    st.session_state.industry_name = ""

if "region" not in st.session_state:
    st.session_state.region = ""

if "topic_text" not in st.session_state:
    st.session_state.topic_text = ""
    
if "before_improve_result" not in st.session_state:
    st.session_state.before_improve_result = ""

if "after_improve_result" not in st.session_state:
    st.session_state.after_improve_result = ""

if "quality_check_result" not in st.session_state:
    st.session_state.quality_check_result = ""

if "project_summary" not in st.session_state:
    st.session_state.project_summary = {}

if "agent_pipeline_report" not in st.session_state:
    st.session_state.agent_pipeline_report = ""

if generate or agent_generate:
    if model_mode == "고품질 모드" and not high_quality_confirmed:
        st.warning("고품질 모드를 사용하려면 비용 확인 체크박스를 선택해주세요.")
        st.stop()

    if industry_choice == "직접 입력":
        if not custom_industry.strip():
            st.warning("직접 입력 업종을 입력해주세요.")
            st.stop()

        industry_name = custom_industry.strip()
        industry = custom_industry_profile(industry_name)
    else:
        industry_name = industry_choice
        industry = industries[industry_choice]
    if not topic.strip():
        topic_text = f"{industry_name} 사장님이 인스타를 해야 하는 이유"
    else:
        topic_text = topic.strip()        

    brand_display = brand_name.strip() if brand_name.strip() else "미입력"
    creative_direction = random.choice(
        [
            "제품 클로즈업 중심",
            "공간 분위기 중심",
            "손님 시점의 발견 장면",
            "영업 준비 과정 중심",
            "문제 상황과 해결 대비",
            "지역 골목 감성 중심",
            "고급 잡지 화보 느낌",
            "현실적인 다큐멘터리 느낌",
            "빛과 그림자를 활용한 시네마틱 구도",
            "작은 소품으로 업종 분위기를 보여주는 장면",
        ]
    )
    creative_seed = random.randint(1000, 9999)

    if agent_generate:
        agent_context = {
            "content_goal": content_goal,
            "topic_text": topic_text,
            "brand_display": brand_display,
            "region_display": region.strip() if region.strip() else "미입력",
            "industry_name": industry_name,
            "target": industry["target"],
            "pain": industry["pain"],
            "visual": industry.get("visual", f"{industry_name} 특유의 공간, 상품, 도구, 소품, 조명, 고객이 실제로 보는 장면"),
            "tone": industry["tone"],
            "content_style": content_style,
            "prompt_preset": prompt_preset,
            "creativity_mode": creativity_mode,
            "video_length": video_length,
            "platform": platform,
        }

        with st.spinner("분야별 에이전트가 순서대로 작업하는 중입니다..."):
            agent_pipeline = run_showpark_agent_pipeline(
                client,
                selected_model,
                agent_context,
            )

        result = agent_pipeline["result"]
        st.session_state.agent_pipeline_report = agent_pipeline["agent_report"]
    else:
        st.session_state.agent_pipeline_report = ""
        prompt = f"""
    중요:
반드시 아래 10개 목차를 모두 작성한다.
중간에 생략하거나 일부 항목만 작성하지 않는다.
특히 #1~#5 콘텐츠 기획 내용을 먼저 작성하고,
#6 이미지 프롬프트와 #7 영상 프롬프트는 마지막에 작성한다.
너는 숏폼 콘텐츠 제작 대행사 'ShowPark'의 콘텐츠 전략가야.
모든 답변은 한국어로 작성해.

[입력 정보]
주제: {topic_text}
고객명/브랜드명: {brand_display}
지역: {region.strip() if region.strip() else "미입력"}
업종: {industry_name}
타깃: {industry["target"]}
고객의 현실 문제: {industry["pain"]}
업종 시각 요소: {industry.get("visual", f"{industry_name} 특유의 공간, 상품, 도구, 소품, 조명, 고객이 실제로 보는 장면")}
기본 톤: {industry["tone"]}
콘텐츠 스타일: {content_style}
프롬프트 프리셋: {prompt_preset}
창의성 모드: {creativity_mode}
이번 생성의 창의 방향: {creative_direction}
반복 방지 번호: {creative_seed}
콘텐츠 목적: {content_goal}
영상 길이: {video_length}
생성할 결과 유형: {output_type}
게시 플랫폼: {platform}

[중요 업종 고정 규칙]
- 사용자가 입력한 업종명 "{industry_name}"은 고유한 업종으로 취급한다.
- "{industry_name}"을 절대 더 넓은 상위 개념으로 바꾸지 말 것.
- 직접 입력 업종을 "레스토랑", "음식점", "외식업", "매장", "샵", "로컬 비즈니스"처럼 뭉뚱그려 표현하지 말 것.
- 사용자가 "라멘집"이라고 입력했다면 "레스토랑", "식당", "일식당", "음식점", "요식업"이라고 부르지 말 것.
- "라멘집"의 경우 반드시 라멘 그릇, 일본식 주방, 라멘 바 좌석, 김이 나는 국물, 차슈, 면, 돈코츠/쇼유/시오 라멘, 좁지만 활기 있는 라멘집 분위기를 반영할 것.
- 사용자가 "치킨집"이라고 입력했다면 치킨집으로 유지하고, 튀김 소리, 포장 박스, 배달 봉투, 치킨 무, 가족형 매장 분위기 등을 반영할 것.
- 사용자가 "한의원"이라고 입력했다면 병원으로 바꾸지 말고, 맥진, 한약, 침구실, 차분한 상담 공간, 한방차 분위기를 반영할 것.
- 업종명 "{industry_name}"은 썸네일, 대본, 캡션, 이미지 프롬프트, 영상 프롬프트, 장면표, 해시태그, 제작 주의사항에 모두 자연스럽게 반영할 것.
- 상위 개념은 보조 설명으로만 사용할 수 있고, 핵심 표현은 반드시 "{industry_name}"으로 유지할 것.

[작성 원칙]
- 모든 답변은 한국어로 작성할 것.
- 영어 프롬프트가 필요한 항목에서만 영어를 함께 제공할 것.
- 광고 티를 너무 내지 말 것.
- 사장님 입장에서 공감되는 현실을 먼저 건드릴 것.
- 어려운 마케팅 용어를 사용하지 말 것.
- 문장은 짧고 강하게 작성할 것.
- 얼굴 노출 없이 만들 수 있는 구성으로 작성할 것.
- 결과물은 바로 복사해서 사용할 수 있게 작성할 것.
- 지역이 입력된 경우 해당 지역의 로컬 고객이 공감할 수 있게 자연스럽게 반영할 것.
- 지역명을 억지로 반복하지 말고, 필요한 곳에만 사용할 것.
- 콘텐츠 목적 "{content_goal}"에 맞게 후킹, 대본, 캡션, 이미지/영상 프롬프트의 강조점을 조정할 것.
- 신규 고객 유입 목적이면 처음 보는 사람이 멈춰볼 만한 이유를 강조할 것.
- 문의/예약 전환 목적이면 자연스럽게 문의, 예약, 방문 행동으로 이어지게 작성할 것.
- 브랜드 신뢰도 상승 목적이면 과장보다 분위기, 꾸준함, 전문성, 실제감을 강조할 것.
- 메뉴/상품 홍보 목적이면 제품의 구체적인 매력, 사용 장면, 먹고 싶은 포인트를 강조할 것.
- 이벤트/할인 홍보 목적이면 혜택은 분명하게 쓰되 싸구려 광고처럼 보이지 않게 할 것.
- 단골 고객 재방문 유도 목적이면 익숙함, 기억, 다시 방문할 이유를 강조할 것.
- 게시 플랫폼 "{platform}"의 특성에 맞게 문장 길이, 후킹 방식, 캡션 흐름을 조정할 것.
- 인스타 릴스는 저장/공유/문의 전환을 고려해서 작성할 것.
- 유튜브 쇼츠는 초반 1초 후킹과 검색형 제목감을 고려해서 작성할 것.
- 틱톡은 더 짧고 직관적이며 반응을 유도하는 말투로 작성할 것.
- 공통 숏폼은 어느 플랫폼에 올려도 어색하지 않게 작성할 것.

[프롬프트 프리셋 규칙]
- 선택한 프리셋은 "{prompt_preset}"이다.
- "기본형"이면 균형 잡힌 실사용 결과를 작성할 것.
- "고객 설득형"이면 고객의 고민, 불안, 선택 이유를 설득력 있게 풀어낼 것.
- "조회수 후킹형"이면 첫 문장, 썸네일, 자막 문구의 멈춤 효과를 가장 강하게 만들 것.
- "브랜드 고급형"이면 과장된 판매 문구보다 신뢰감, 분위기, 전문성, 디테일을 강조할 것.
- "자영업자 공감형"이면 사장님이 실제로 겪는 현실 문제와 감정에 더 깊게 공감할 것.
- "전환 집중형"이면 문의, 예약, 방문, 저장, 공유 같은 다음 행동으로 자연스럽게 이어지게 작성할 것.

[창의성 모드 규칙]
- 선택한 창의성 모드는 "{creativity_mode}"이다.
- 이번 생성에서는 "{creative_direction}" 방향을 이미지 프롬프트와 영상 프롬프트에 자연스럽게 반영할 것.
- 반복 방지 번호 "{creative_seed}"를 참고해 이전에 자주 나올 법한 뻔한 장면을 피할 것.
- "안정형"이면 실사용하기 쉬운 현실적인 장면을 우선할 것.
- "균형형"이면 현실성과 새로움이 함께 느껴지는 장면을 만들 것.
- "창의형"이면 구도, 소품, 조명, 카메라 시점에 더 신선한 변화를 줄 것.
- "실험형"이면 업종 정체성은 유지하되 흔하지 않은 시점, 분위기, 연출을 과감하게 제안할 것.
- 이미지 프롬프트는 같은 주제라도 매번 다른 이미지가 나올 수 있게 공간, 소품, 조명, 구도, 렌즈감, 계절감 중 최소 3가지를 바꿔 제안할 것.

[결과 유형 규칙]
- 사용자가 선택한 생성할 결과 유형은 "{output_type}"이다.
- "{output_type}"이 "전체 패키지"라면 아래 출력 형식을 모두 작성할 것.
- "{output_type}"이 "릴스 대본만"이라면 # 3. 릴스 3문장 대본 5개만 작성할 것.
- "{output_type}"이 "이미지 프롬프트만"이라면 # 6. 이미지 생성 프롬프트만 작성할 것.
- "{output_type}"이 "영상 프롬프트만"이라면 # 7. 영상 생성 프롬프트와 # 8. 장면 구성표만 작성할 것.
- "{output_type}"이 "인스타 캡션만"이라면 # 4. 인스타 캡션 3개만 작성할 것.
- "{output_type}"이 "해시태그만"이라면 # 5. 해시태그 20개만 작성할 것.
- 선택한 결과 유형과 관계없는 항목은 출력하지 말 것.
[출력 형식]

# 1. 콘텐츠 방향 요약
- 어떤 사장님을 겨냥하는지
- 어떤 감정을 건드리는지
- 어떤 행동을 유도하는지

# 2. 썸네일 문구 10개
- 10자 내외
- 강한 후킹
- 업종 사장님이 멈춰볼 문장

# 3. 릴스 3문장 대본 5개
- 1문장: 후킹
- 2문장: 현실 문제
- 3문장: 캡션 확인 또는 문의 유도
- 얼굴 노출 없는 나레이션 형식

# 4. 인스타 캡션 3개
- 첫 줄 강한 후킹
- 본문은 3~5줄
- 마지막은 자연스러운 문의 유도

# 5. 해시태그 20개
- 게시 플랫폼 "{platform}"에 맞는 해시태그로 작성
- 업종 해시태그
- 지역 해시태그
- 콘텐츠 주제 해시태그
- 너무 넓은 해시태그만 반복하지 말 것

# 6. 이미지 생성 프롬프트
조건:
- 서로 다른 이미지 프롬프트 변형안 3개 작성
- 각 변형안은 구도, 조명, 소품, 분위기, 카메라 시점이 서로 다르게 보이게 작성
- 9:16 세로 이미지
- 얼굴 노출 없음
- 입력 업종을 절대 일반화하지 말 것
- 업종 특유의 공간, 제품, 메뉴, 소품, 분위기를 구체적으로 반영할 것
- 각 변형안마다 한국어 프롬프트와 영어 프롬프트를 함께 작성
- 마지막에 공통으로 피해야 할 표현도 함께 작성

# 7. 영상 생성 프롬프트
조건:
- {video_length} 분량
- 9:16 세로 영상
- 얼굴 노출 없음
- 입력 업종을 절대 일반화하지 말 것
- 업종 특유의 공간, 제품, 메뉴, 소품, 분위기를 구체적으로 반영할 것
- 카메라 움직임 포함
- 장면 순서 포함
- 한국어 프롬프트
- 영어 프롬프트

# 8. 장면 구성표
| 시간 | 장면 | 화면 설명 | 자막 |
| 0~2초 |  |  |  |
| 2~5초 |  |  |  |
| 5초 이후 |  |  |  |

# 9. 추천 자막 문구 10개

# 10. 제작 시 주의사항
- 피해야 할 표현
- 피해야 할 장면
- 더 자연스럽게 보이게 하는 팁
"""

        with st.spinner("AI가 콘텐츠 패키지를 생성 중입니다..."):
            result = ask_ai(prompt, selected_model)

    st.session_state.result = result
    st.session_state.industry_name = industry_name
    st.session_state.region = region
    st.session_state.topic_text = topic_text
    st.session_state.project_summary = {
        "콘텐츠 목적": content_goal,
        "콘텐츠 주제": topic_text,
        "고객명/브랜드명": brand_display,
        "지역": region.strip() if region.strip() else "미입력",
        "업종": industry_name,
        "콘텐츠 스타일": content_style,
        "프롬프트 프리셋": prompt_preset,
        "창의성 모드": creativity_mode,
        "영상 길이": video_length,
        "생성 결과 유형": output_type,
        "게시 플랫폼": platform,
        "AI 모델": model_mode,
        "생성 방식": "분야별 에이전트" if agent_generate else "일반 생성",
    }

    saved_file = save_result(
        result,
        industry_name,
        region,
        topic_text,
    )

    st.session_state.generate_count += 1

    with usage_placeholder.container():
        usage_col1, usage_col2 = st.columns(2)
        usage_col1.metric("오늘 생성 횟수", f"{st.session_state.generate_count}회")
        usage_col2.metric("오늘 다듬기 횟수", f"{st.session_state.improve_count}회")

    st.success("생성 완료!")
    st.info(f"저장 완료: {saved_file}")

if st.session_state.result:
    sections = split_result_sections(st.session_state.result)

    if st.session_state.project_summary:
        with st.container(border=True):
            st.markdown("### 작업 요약")
            summary_items = list(st.session_state.project_summary.items())

            for index in range(0, len(summary_items), 3):
                cols = st.columns(3)
                for col, (label, value) in zip(cols, summary_items[index:index + 3]):
                    col.caption(label)
                    col.markdown(f"**{value}**")

            summary_text = "\n".join(
                f"{label}: {value}"
                for label, value in st.session_state.project_summary.items()
            )
            section_download_button(
                "작업 요약 TXT 다운로드",
                summary_text,
                "project_summary",
                "download_project_summary",
            )

    if st.session_state.agent_pipeline_report:
        with st.expander("분야별 에이전트 작업 기록", expanded=False):
            st.text_area(
                "에이전트 작업 기록 복사용",
                value=st.session_state.agent_pipeline_report,
                height=420,
                key="copy_agent_pipeline_report",
            )
            section_download_button(
                "에이전트 작업 기록 TXT 다운로드",
                st.session_state.agent_pipeline_report,
                "agent_pipeline_report",
                "download_agent_pipeline_report",
            )

    result_tabs = st.tabs(
        [
            "콘텐츠 방향",
            "썸네일 문구",
            "릴스 대본",
            "이미지 프롬프트",
            "영상 프롬프트",
            "캡션",
            "해시태그",
            "자막 문구",
            "제작 노트",
            "체크리스트",
            "작업 세트",
            "전체 결과",
        ]
    )

    with result_tabs[0]:
        direction_text = get_sections_text(sections, [1])
        if direction_text:
            st.markdown(direction_text)
        else:
            st.info("콘텐츠 방향 섹션을 찾지 못했습니다.")
        st.text_area(
            "콘텐츠 방향 복사용",
            value=direction_text,
            height=260,
            key="copy_content_direction",
        )
        section_download_button(
            "콘텐츠 방향 TXT 다운로드",
            direction_text,
            "content_direction",
            "download_content_direction",
        )

        if st.button("콘텐츠 방향만 새로 생성", key="regen_content_direction_button"):
            with st.spinner("콘텐츠 방향만 새롭게 다시 만드는 중입니다..."):
                new_direction = regenerate_content_direction(
                    st.session_state.result,
                    direction_text,
                    selected_model,
                )

            st.session_state.before_improve_result = st.session_state.result
            st.session_state.after_improve_result = new_direction
            st.session_state.result = replace_result_section(
                st.session_state.result,
                1,
                new_direction,
            )

            saved_file = save_result(
                st.session_state.result,
                st.session_state.industry_name,
                st.session_state.region,
                st.session_state.topic_text,
            )

            st.session_state.improve_count += 1
            st.success("콘텐츠 방향을 새로 생성했습니다.")
            st.info(f"저장 완료: {saved_file}")
            st.rerun()

    with result_tabs[1]:
        thumbnail_text = get_sections_text(sections, [2])
        if thumbnail_text:
            st.markdown(thumbnail_text)
        else:
            st.info("썸네일 문구 섹션을 찾지 못했습니다.")
        st.text_area(
            "썸네일 문구 복사용",
            value=thumbnail_text,
            height=260,
            key="copy_thumbnail_hooks",
        )
        section_download_button(
            "썸네일 문구 TXT 다운로드",
            thumbnail_text,
            "thumbnail_hooks",
            "download_thumbnail_hooks",
        )

        if st.button("썸네일 문구만 새로 생성", key="regen_thumbnail_hooks_button"):
            with st.spinner("썸네일 문구만 새롭게 다시 만드는 중입니다..."):
                new_thumbnail_hooks = regenerate_thumbnail_hooks(
                    st.session_state.result,
                    thumbnail_text,
                    selected_model,
                )

            st.session_state.before_improve_result = st.session_state.result
            st.session_state.after_improve_result = new_thumbnail_hooks
            st.session_state.result = replace_result_section(
                st.session_state.result,
                2,
                new_thumbnail_hooks,
            )

            saved_file = save_result(
                st.session_state.result,
                st.session_state.industry_name,
                st.session_state.region,
                st.session_state.topic_text,
            )

            st.session_state.improve_count += 1
            st.success("썸네일 문구를 새로 생성했습니다.")
            st.info(f"저장 완료: {saved_file}")
            st.rerun()

    with result_tabs[2]:
        reels_text = get_sections_text(sections, [3])
        if reels_text:
            st.markdown(reels_text)
        else:
            st.info("릴스 대본 섹션을 찾지 못했습니다.")
        st.text_area(
            "릴스 대본 복사용",
            value=reels_text,
            height=320,
            key="copy_reels_script",
        )
        section_download_button(
            "릴스 대본 TXT 다운로드",
            reels_text,
            "reels_script",
            "download_reels_script",
        )

        if st.button("릴스 대본만 새로 생성", key="regen_reels_script_button"):
            with st.spinner("릴스 대본만 새롭게 다시 만드는 중입니다..."):
                new_reels_script = regenerate_reels_script(
                    st.session_state.result,
                    reels_text,
                    selected_model,
                )

            st.session_state.before_improve_result = st.session_state.result
            st.session_state.after_improve_result = new_reels_script
            st.session_state.result = replace_result_section(
                st.session_state.result,
                3,
                new_reels_script,
            )

            saved_file = save_result(
                st.session_state.result,
                st.session_state.industry_name,
                st.session_state.region,
                st.session_state.topic_text,
            )

            st.session_state.improve_count += 1
            st.success("릴스 대본을 새로 생성했습니다.")
            st.info(f"저장 완료: {saved_file}")
            st.rerun()

    with result_tabs[3]:
        image_prompt_text = get_sections_text(sections, [6])
        if image_prompt_text:
            st.markdown(image_prompt_text)
        else:
            st.info("이미지 프롬프트 섹션을 찾지 못했습니다.")

        st.divider()
        st.caption("아래 박스에서 이미지 생성툴에 붙여넣을 프롬프트를 복사하세요.")
        st.text_area(
            "이미지 프롬프트 복사용",
            value=image_prompt_text,
            height=320,
            key="copy_image_prompt",
        )
        section_download_button(
            "이미지 프롬프트 TXT 다운로드",
            image_prompt_text,
            "image_prompt",
            "download_image_prompt",
        )

        if st.button("이미지 프롬프트만 새로 생성", key="regen_image_prompt_button"):
            with st.spinner("이미지 프롬프트만 새롭게 다시 만드는 중입니다..."):
                new_image_prompt = regenerate_image_prompt(
                    st.session_state.result,
                    image_prompt_text,
                    creativity_mode,
                    selected_model,
                )

            st.session_state.before_improve_result = st.session_state.result
            st.session_state.after_improve_result = new_image_prompt
            st.session_state.result = replace_result_section(
                st.session_state.result,
                6,
                new_image_prompt,
            )

            saved_file = save_result(
                st.session_state.result,
                st.session_state.industry_name,
                st.session_state.region,
                st.session_state.topic_text,
            )

            st.session_state.improve_count += 1
            st.success("이미지 프롬프트를 새로 생성했습니다.")
            st.info(f"저장 완료: {saved_file}")
            st.rerun()

    with result_tabs[4]:
        video_prompt_text = get_sections_text(sections, [7, 8])
        if video_prompt_text:
            st.markdown(video_prompt_text)
        else:
            st.info("영상 프롬프트 섹션을 찾지 못했습니다.")
        st.text_area(
            "영상 프롬프트 복사용",
            value=video_prompt_text,
            height=320,
            key="copy_video_prompt",
        )
        section_download_button(
            "영상 프롬프트 TXT 다운로드",
            video_prompt_text,
            "video_prompt",
            "download_video_prompt",
        )

        if st.button("영상 프롬프트만 새로 생성", key="regen_video_prompt_button"):
            with st.spinner("영상 프롬프트만 새롭게 다시 만드는 중입니다..."):
                new_video_prompt = regenerate_video_prompt(
                    st.session_state.result,
                    video_prompt_text,
                    creativity_mode,
                    selected_model,
                )

            st.session_state.before_improve_result = st.session_state.result
            st.session_state.after_improve_result = new_video_prompt
            st.session_state.result = replace_result_section_range(
                st.session_state.result,
                7,
                8,
                new_video_prompt,
            )

            saved_file = save_result(
                st.session_state.result,
                st.session_state.industry_name,
                st.session_state.region,
                st.session_state.topic_text,
            )

            st.session_state.improve_count += 1
            st.success("영상 프롬프트를 새로 생성했습니다.")
            st.info(f"저장 완료: {saved_file}")
            st.rerun()

    with result_tabs[5]:
        caption_text = get_sections_text(sections, [4])
        if caption_text:
            st.markdown(caption_text)
        else:
            st.info("캡션 섹션을 찾지 못했습니다.")
        st.text_area(
            "캡션 복사용",
            value=caption_text,
            height=320,
            key="copy_caption",
        )
        section_download_button(
            "캡션 TXT 다운로드",
            caption_text,
            "caption",
            "download_caption",
        )

        if st.button("캡션만 새로 생성", key="regen_caption_button"):
            with st.spinner("캡션만 새롭게 다시 만드는 중입니다..."):
                new_caption = regenerate_caption(
                    st.session_state.result,
                    caption_text,
                    selected_model,
                )

            st.session_state.before_improve_result = st.session_state.result
            st.session_state.after_improve_result = new_caption
            st.session_state.result = replace_result_section(
                st.session_state.result,
                4,
                new_caption,
            )

            saved_file = save_result(
                st.session_state.result,
                st.session_state.industry_name,
                st.session_state.region,
                st.session_state.topic_text,
            )

            st.session_state.improve_count += 1
            st.success("캡션을 새로 생성했습니다.")
            st.info(f"저장 완료: {saved_file}")
            st.rerun()

    with result_tabs[6]:
        hashtag_text = get_sections_text(sections, [5])
        if hashtag_text:
            st.markdown(hashtag_text)
        else:
            st.info("해시태그 섹션을 찾지 못했습니다.")
        st.text_area(
            "해시태그 복사용",
            value=hashtag_text,
            height=260,
            key="copy_hashtags",
        )
        section_download_button(
            "해시태그 TXT 다운로드",
            hashtag_text,
            "hashtags",
            "download_hashtags",
        )

        if st.button("해시태그만 새로 생성", key="regen_hashtags_button"):
            with st.spinner("해시태그만 새롭게 다시 만드는 중입니다..."):
                new_hashtags = regenerate_hashtags(
                    st.session_state.result,
                    hashtag_text,
                    selected_model,
                )

            st.session_state.before_improve_result = st.session_state.result
            st.session_state.after_improve_result = new_hashtags
            st.session_state.result = replace_result_section(
                st.session_state.result,
                5,
                new_hashtags,
            )

            saved_file = save_result(
                st.session_state.result,
                st.session_state.industry_name,
                st.session_state.region,
                st.session_state.topic_text,
            )

            st.session_state.improve_count += 1
            st.success("해시태그를 새로 생성했습니다.")
            st.info(f"저장 완료: {saved_file}")
            st.rerun()

    with result_tabs[7]:
        subtitle_text = get_sections_text(sections, [9])
        if subtitle_text:
            st.markdown(subtitle_text)
        else:
            st.info("자막 문구 섹션을 찾지 못했습니다.")
        st.text_area(
            "자막 문구 복사용",
            value=subtitle_text,
            height=260,
            key="copy_subtitle_lines",
        )
        section_download_button(
            "자막 문구 TXT 다운로드",
            subtitle_text,
            "subtitle_lines",
            "download_subtitle_lines",
        )

        if st.button("자막 문구만 새로 생성", key="regen_subtitle_lines_button"):
            with st.spinner("자막 문구만 새롭게 다시 만드는 중입니다..."):
                new_subtitle_lines = regenerate_subtitle_lines(
                    st.session_state.result,
                    subtitle_text,
                    selected_model,
                )

            st.session_state.before_improve_result = st.session_state.result
            st.session_state.after_improve_result = new_subtitle_lines
            st.session_state.result = replace_result_section(
                st.session_state.result,
                9,
                new_subtitle_lines,
            )

            saved_file = save_result(
                st.session_state.result,
                st.session_state.industry_name,
                st.session_state.region,
                st.session_state.topic_text,
            )

            st.session_state.improve_count += 1
            st.success("자막 문구를 새로 생성했습니다.")
            st.info(f"저장 완료: {saved_file}")
            st.rerun()

    with result_tabs[8]:
        production_note_text = get_sections_text(sections, [10])
        if production_note_text:
            st.markdown(production_note_text)
        else:
            st.info("제작 노트 섹션을 찾지 못했습니다.")
        st.text_area(
            "제작 노트 복사용",
            value=production_note_text,
            height=260,
            key="copy_production_notes",
        )
        section_download_button(
            "제작 노트 TXT 다운로드",
            production_note_text,
            "production_notes",
            "download_production_notes",
        )

        if st.button("제작 노트만 새로 생성", key="regen_production_notes_button"):
            with st.spinner("제작 노트만 새롭게 다시 만드는 중입니다..."):
                new_production_notes = regenerate_production_notes(
                    st.session_state.result,
                    production_note_text,
                    selected_model,
                )

            st.session_state.before_improve_result = st.session_state.result
            st.session_state.after_improve_result = new_production_notes
            st.session_state.result = replace_result_section(
                st.session_state.result,
                10,
                new_production_notes,
            )

            saved_file = save_result(
                st.session_state.result,
                st.session_state.industry_name,
                st.session_state.region,
                st.session_state.topic_text,
            )

            st.session_state.improve_count += 1
            st.success("제작 노트를 새로 생성했습니다.")
            st.info(f"저장 완료: {saved_file}")
            st.rerun()

    with result_tabs[9]:
        checklist_text = f"""# 쇼츠/릴스 제작 체크리스트

## 1. 기획 확인
- 콘텐츠 목적이 명확한가?
- 첫 1초 안에 멈춰볼 후킹이 있는가?
- 업종과 지역 분위기가 반영되어 있는가?
- 광고 느낌이 과하지 않은가?

## 2. 제작 준비
- 썸네일 문구를 1개 선택했는가?
- 사용할 릴스 대본을 1개 선택했는가?
- 이미지 프롬프트와 영상 프롬프트를 따로 복사했는가?
- 얼굴 노출 없음 조건이 프롬프트에 들어갔는가?

## 3. 게시 준비
- 캡션 첫 줄이 강한가?
- 해시태그가 업종/지역/릴스 목적에 맞는가?
- 자막 문구가 짧고 읽기 쉬운가?
- 문의 또는 저장 유도 문장이 있는가?

## 4. 최종 확인
- 9:16 세로 비율로 제작했는가?
- 영상 길이가 선택한 길이에 맞는가?
- 브랜드명/지역명 오타가 없는가?
- 업로드 전에 모바일 화면에서 한 번 확인했는가?
"""
        st.text_area(
            "체크리스트 복사용",
            value=checklist_text,
            height=420,
            key="copy_workflow_checklist",
        )
        section_download_button(
            "체크리스트 TXT 다운로드",
            checklist_text,
            "workflow_checklist",
            "download_workflow_checklist",
        )

    with result_tabs[10]:
        posting_set_text = "\n\n".join(
            part
            for part in [
                f"## 썸네일 문구\n{thumbnail_text}" if thumbnail_text else "",
                f"## 릴스 대본\n{reels_text}" if reels_text else "",
                f"## 캡션\n{caption_text}" if caption_text else "",
                f"## 해시태그\n{hashtag_text}" if hashtag_text else "",
            ]
            if part.strip()
        )
        production_set_text = "\n\n".join(
            part
            for part in [
                f"## 이미지 프롬프트\n{image_prompt_text}" if image_prompt_text else "",
                f"## 영상 프롬프트\n{video_prompt_text}" if video_prompt_text else "",
                f"## 자막 문구\n{subtitle_text}" if subtitle_text else "",
                f"## 제작 노트\n{production_note_text}" if production_note_text else "",
            ]
            if part.strip()
        )

        set_col1, set_col2 = st.columns(2)

        with set_col1:
            st.markdown("#### 게시용 세트")
            st.text_area(
                "게시용 세트 복사용",
                value=posting_set_text,
                height=360,
                key="copy_posting_set",
            )
            section_download_button(
                "게시용 세트 TXT 다운로드",
                posting_set_text,
                "posting_set",
                "download_posting_set",
            )

        with set_col2:
            st.markdown("#### 제작용 세트")
            st.text_area(
                "제작용 세트 복사용",
                value=production_set_text,
                height=360,
                key="copy_production_set",
            )
            section_download_button(
                "제작용 세트 TXT 다운로드",
                production_set_text,
                "production_set",
                "download_production_set",
            )

    with result_tabs[11]:
        st.markdown(st.session_state.result)
        st.text_area(
            "전체 결과 복사용",
            value=st.session_state.result,
            height=400,
            key="copy_full_result",
        )
        section_download_button(
            "전체 결과 TXT 다운로드",
            st.session_state.result,
            "full_result",
            "download_full_result",
        )

    if st.button("현재 결과 지우기", key="clear_result_button"):
        st.session_state.result = ""
        st.session_state.industry_name = ""
        st.session_state.region = ""
        st.session_state.topic_text = ""
        st.session_state.before_improve_result = ""
        st.session_state.after_improve_result = ""
        st.session_state.quality_check_result = ""
        st.session_state.project_summary = {}
        st.session_state.agent_pipeline_report = ""
        st.rerun()

    st.divider()
    st.subheader("결과 다듬기")

    if st.button("에이전트로 최종본 만들기", key="agent_finalize_button"):
        with st.spinner("에이전트가 품질 검사 후 최종본으로 자동 개선하는 중입니다..."):
            quality_report = check_content_quality(
                st.session_state.result,
                st.session_state.industry_name,
                st.session_state.region,
                st.session_state.topic_text,
                selected_model,
            )
            finalized_result = agent_finalize_result(
                st.session_state.result,
                quality_report,
                selected_model,
            )

        st.session_state.quality_check_result = quality_report
        st.session_state.before_improve_result = st.session_state.result
        st.session_state.after_improve_result = finalized_result
        st.session_state.result = finalized_result

        finalized_saved_file = save_result(
            finalized_result,
            st.session_state.industry_name,
            st.session_state.region,
            st.session_state.topic_text,
        )

        st.session_state.improve_count += 1

        st.success("에이전트 최종본 생성 완료!")
        st.info(f"최종본 저장 완료: {finalized_saved_file}")
        st.rerun()

    if st.button("현재 결과 품질 검사", key="quality_check_button"):
        with st.spinner("AI가 현재 결과를 검수하는 중입니다..."):
            st.session_state.quality_check_result = check_content_quality(
                st.session_state.result,
                st.session_state.industry_name,
                st.session_state.region,
                st.session_state.topic_text,
                selected_model,
            )

    if st.session_state.quality_check_result:
        st.markdown(st.session_state.quality_check_result)
        st.text_area(
            "품질 검사 결과 복사용",
            value=st.session_state.quality_check_result,
            height=300,
            key="copy_quality_check_result",
        )
        section_download_button(
            "품질 검사 결과 TXT 다운로드",
            st.session_state.quality_check_result,
            "quality_check",
            "download_quality_check",
        )

    improve_type = st.selectbox(
        "어떻게 다듬을까요?",
        [
            "더 짧고 강하게",
            "더 자연스럽게",
            "더 고급스럽게",
            "더 직설적으로",
            "이미지 프롬프트를 더 구체적으로",
            "영상 프롬프트를 더 구체적으로",
        ],
        key="improve_type_select",
    )

    if st.button("선택한 방향으로 다시 다듬기", key="improve_button"):
        with st.spinner("AI가 결과를 다시 다듬는 중입니다..."):
            improved_result = improve_result(
                st.session_state.result,
                improve_type,
                selected_model,
            )

        st.session_state.before_improve_result = st.session_state.result
        st.session_state.after_improve_result = improved_result
        st.session_state.result = improved_result

        improved_saved_file = save_result(
            improved_result,
            st.session_state.industry_name,
            st.session_state.region,
            st.session_state.topic_text,
        )

        st.session_state.improve_count += 1

        st.success("다듬기 완료!")
        st.info(f"다듬은 결과 저장 완료: {improved_saved_file}")
        st.rerun()

    if st.session_state.before_improve_result and st.session_state.after_improve_result:
        st.divider()
        st.subheader("다듬기 전 / 후 비교")

        before_col, after_col = st.columns(2)

        with before_col:
            st.markdown("### 다듬기 전")
            st.text_area(
                "원본 결과",
                value=st.session_state.before_improve_result,
                height=350,
                key="before_improve_text",
            )

        with after_col:
            st.markdown("### 다듬기 후")
            st.text_area(
                "개선된 결과",
                value=st.session_state.after_improve_result,
                height=350,
                key="after_improve_text",
            )


