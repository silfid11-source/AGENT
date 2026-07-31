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
