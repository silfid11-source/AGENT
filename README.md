# ShowPark AI Studio

ShowPark AI Studio는 숏폼 콘텐츠 제작을 돕는 개인용 Streamlit 웹앱입니다.

## 주요 기능

- 업종, 지역, 콘텐츠 목적 기반 릴스 콘텐츠 패키지 생성
- 썸네일 문구, 릴스 대본, 캡션, 해시태그 생성
- 이미지 프롬프트와 영상 프롬프트 생성
- 품질 검사 및 자동 개선
- 분야별 에이전트 파이프라인
- 다크 모드 UI

## 실행 방법

1. `.env.example` 파일을 복사해서 `.env` 파일을 만듭니다.
2. `.env` 안에 OpenAI API 키를 입력합니다.
3. 필요한 패키지를 설치합니다.

```powershell
pip install -r requirements.txt
```

4. 앱을 실행합니다.

```powershell
streamlit run app_v2.py
```

## 중요한 보안 주의

`.env` 파일에는 API 키가 들어갑니다.
이 파일은 GitHub에 올리면 안 됩니다.
현재 `.gitignore`에서 `.env`, `.venv`, 생성 결과 폴더가 제외되도록 설정되어 있습니다.

## 파일 구성

- `app_v2.py`: 메인 Streamlit 앱
- `agents.py`: 분야별 에이전트 파이프라인
- `agent_rules.py`: 에이전트 공통 규칙과 작업 지침
- `reference_analyzer.py`: 레퍼런스 예시를 분석해서 에이전트 규칙으로 바꾸는 자동화
- `references`: 레퍼런스 예시를 넣는 폴더
- `workflows.py`: 화면 없이 실행하는 자동화 워크플로우 로직
- `run_workflow.py`: 자동화 워크플로우 실행 파일
- `workflow_inputs.csv`: 자동화에 사용할 콘텐츠 입력 목록
- `run_showpark.bat`: 현재 PC에서 앱을 쉽게 실행하기 위한 배치 파일
- `.streamlit/config.toml`: 다크 모드 테마 설정
- `requirements.txt`: 필요한 Python 패키지 목록

## 화면 없이 자동화 실행

`workflow_inputs.csv`에 만들 콘텐츠 목록을 적고 아래 명령으로 실행할 수 있습니다.

먼저 API 호출 없이 입력만 점검하려면:

```powershell
python run_workflow.py --dry-run
```

실제로 콘텐츠를 생성하려면:

```powershell
python run_workflow.py
```

결과는 `workflow_outputs` 폴더에 저장됩니다.

## 레퍼런스 학습형 자동화

마음에 드는 예시를 `references` 폴더에 넣어두면 에이전트가 먼저 스타일을 분석한 뒤 결과물에 반영할 수 있습니다.

사용할 수 있는 폴더:

- `references/brand_guides`: 브랜드 톤, 금지 표현, 고객 정보
- `references/captions`: 인스타 캡션 예시
- `references/scripts`: 릴스 대본 예시
- `references/image_prompts`: 이미지 프롬프트 예시
- `references/video_prompts`: 영상 프롬프트 예시
- `references/urls.txt`: 참고하고 싶은 웹페이지 URL 목록

API 호출 없이 폴더와 입력값만 점검하려면:

```powershell
python run_workflow.py --analyze-references --dry-run
```

레퍼런스를 분석하고 자동화를 실행하려면:

```powershell
python run_workflow.py --analyze-references
```

분석 결과는 `reference_rules.md`에 저장되고, 이후 에이전트들이 자동으로 참고합니다.
고객 레퍼런스 원본과 분석 결과는 GitHub에 올라가지 않도록 제외되어 있습니다.

URL 레퍼런스를 쓰려면 `references/urls.example.txt`를 복사해서 `references/urls.txt`를 만들고, URL을 한 줄에 하나씩 넣으면 됩니다.
