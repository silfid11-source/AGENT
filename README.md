# ShowPark AI Studio

ShowPark AI Studio는 업종, 지역, 콘텐츠 목적을 바탕으로 숏폼 콘텐츠 패키지를 만드는 Streamlit 앱입니다.

## 주요 기능

- 업종/지역/목적 기반 숏폼 콘텐츠 패키지 생성
- 썸네일 문구, 릴스 대본, 인스타 캡션, 해시태그 생성
- 이미지/영상 프롬프트와 장면 구성표 생성
- 레퍼런스 학습을 통한 브랜드 톤, 캡션, 대본, 프롬프트 스타일 반영
- 자동화 작업 목록 저장, 상태 관리, 필터링
- 자동화 결과 조회와 다운로드

## 실행 방법

1. `.env.example`을 복사해 `.env`를 만듭니다.
2. `.env`에 OpenAI API 키를 입력합니다.
3. 필요한 패키지를 설치합니다.

```powershell
pip install -r requirements.txt
```

4. 앱을 실행합니다.

```powershell
streamlit run app_v2.py
```

## 앱에서 작업하기

### 레퍼런스 학습

앱의 `레퍼런스 바로 추가` 영역에서 다음 자료를 넣을 수 있습니다.

- 텍스트: 브랜드 톤, 캡션 예시, 릴스 대본, 이미지/영상 프롬프트
- URL: 참고하고 싶은 웹페이지 주소
- 이미지: 참고할 이미지 파일과 이미지에서 따라야 할 메모

자료를 넣은 뒤 `레퍼런스 학습 실행`을 누르면 `reference_rules.md`가 생성되고, 이후 콘텐츠 생성에 반영됩니다.

### 자동화 작업 관리

`자동화 작업 관리` 영역에서 여러 콘텐츠 작업을 쌓아둘 수 있습니다.

- 새 작업은 기본 상태가 `대기`입니다.
- 자동화 실행에 성공하면 `완료`로 바뀝니다.
- 실행 중 오류가 나면 `오류`로 바뀝니다.
- 앱에서 상태 필터, 실행 포함/제외, 삭제, 대기 상태 복구를 할 수 있습니다.

### 자동화 결과 확인

`최근 자동화 결과` 영역에서 `workflow_outputs`에 저장된 결과를 앱 안에서 바로 확인하고 다운로드할 수 있습니다.

## 화면 없이 자동화 실행

먼저 API 호출 없이 입력만 점검하려면:

```powershell
python run_workflow.py --dry-run
```

실제로 콘텐츠를 생성하려면:

```powershell
python run_workflow.py
```

레퍼런스를 먼저 분석하고 자동화를 실행하려면:

```powershell
python run_workflow.py --analyze-references
```

결과는 `workflow_outputs` 폴더에 저장됩니다.

## 주요 파일

- `app_v2.py`: 메인 Streamlit 앱
- `agents.py`: 분야별 에이전트 파이프라인
- `agent_rules.py`: 에이전트 공통 규칙
- `reference_analyzer.py`: 레퍼런스 분석 자동화
- `workflows.py`: 화면 없이 실행하는 자동화 워크플로우
- `run_workflow.py`: 자동화 실행 CLI
- `workflow_inputs.csv`: 자동화 작업 입력 목록
- `references/`: 레퍼런스 원본 저장 폴더
- `workflow_outputs/`: 자동화 결과 저장 폴더

## 보안 주의

`.env`에는 API 키가 들어가므로 GitHub에 올리면 안 됩니다.

현재 `.gitignore`는 다음 자료를 제외합니다.

- `.env`, `.streamlit/secrets.toml`
- `.venv/`, `.codex_venv/`
- `projects/`, `results/`, `workflow_outputs/`
- 고객 레퍼런스 원본과 `reference_rules.md`
