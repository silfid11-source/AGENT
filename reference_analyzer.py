from pathlib import Path


REFERENCE_DIRS = [
    "brand_guides",
    "captions",
    "scripts",
    "image_prompts",
    "video_prompts",
]

REFERENCE_RULES_PATH = "reference_rules.md"
SUPPORTED_REFERENCE_EXTENSIONS = {".txt", ".md", ".csv"}


def ensure_reference_folders(base_dir="references"):
    base_path = Path(base_dir)
    base_path.mkdir(exist_ok=True)

    for folder in REFERENCE_DIRS:
        (base_path / folder).mkdir(parents=True, exist_ok=True)

    return base_path


def load_reference_examples(base_dir="references", max_chars=12000):
    base_path = ensure_reference_folders(base_dir)
    blocks = []
    total_chars = 0

    for folder in REFERENCE_DIRS:
        folder_path = base_path / folder
        files = sorted(
            file
            for file in folder_path.iterdir()
            if file.is_file() and file.suffix.lower() in SUPPORTED_REFERENCE_EXTENSIONS
        )

        if not files:
            continue

        folder_blocks = [f"## {folder}"]
        for file in files:
            if total_chars >= max_chars:
                break

            text = file.read_text(encoding="utf-8", errors="ignore").strip()
            if not text:
                continue

            remaining = max_chars - total_chars
            clipped = text[:remaining]
            folder_blocks.append(f"### {file.name}\n{clipped}")
            total_chars += len(clipped)

        if len(folder_blocks) > 1:
            blocks.append("\n\n".join(folder_blocks))

    return "\n\n".join(blocks).strip()


def load_reference_rules(path=REFERENCE_RULES_PATH):
    rules_path = Path(path)
    if not rules_path.exists():
        return ""

    return rules_path.read_text(encoding="utf-8", errors="ignore").strip()


def analyze_references(
    client,
    model_name,
    base_dir="references",
    output_path=REFERENCE_RULES_PATH,
):
    examples = load_reference_examples(base_dir)
    if not examples:
        ensure_reference_folders(base_dir)
        return ""

    prompt = f"""
너는 ShowPark AI Studio의 레퍼런스 분석 에이전트야.
아래 레퍼런스들을 분석해서 앞으로 콘텐츠 에이전트들이 따라야 할 스타일 규칙을 만들어.

[분석 기준]
- 톤과 문체
- 후킹 문장 패턴
- 릴스 대본 구조
- 캡션 구조
- 이미지 프롬프트 스타일
- 영상 프롬프트 스타일
- 반복하면 안 되는 표현
- 반드시 따라야 할 제작 규칙

[출력 형식]
# 레퍼런스 분석 규칙

## 1. 톤과 문체

## 2. 후킹 패턴

## 3. 릴스 대본 구조

## 4. 캡션 구조

## 5. 이미지 프롬프트 스타일

## 6. 영상 프롬프트 스타일

## 7. 피해야 할 표현

## 8. 에이전트 적용 규칙

[레퍼런스]
{examples}
"""

    response = client.responses.create(
        model=model_name,
        input=prompt,
    )
    rules = response.output_text.strip()

    Path(output_path).write_text(rules, encoding="utf-8")
    return rules
