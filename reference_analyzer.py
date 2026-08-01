from html.parser import HTMLParser
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


REFERENCE_DIRS = [
    "brand_guides",
    "captions",
    "scripts",
    "image_prompts",
    "video_prompts",
]

REFERENCE_RULES_PATH = "reference_rules.md"
SUPPORTED_REFERENCE_EXTENSIONS = {".txt", ".md", ".csv"}
URL_REFERENCE_FILE = "urls.txt"


class PageTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data):
        if self.skip_depth:
            return

        text = " ".join(data.split())
        if text:
            self.parts.append(text)

    def get_text(self):
        return "\n".join(self.parts)


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

    url_examples = load_url_reference_examples(base_path, max_chars - total_chars)
    if url_examples:
        blocks.append(url_examples)

    return "\n\n".join(blocks).strip()


def load_reference_urls(base_path):
    url_file = base_path / URL_REFERENCE_FILE
    if not url_file.exists():
        return []

    urls = []
    for line in url_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        if text.startswith(("http://", "https://")):
            urls.append(text)

    return urls


def fetch_url_text(url, max_chars=3000):
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 ShowParkAIStudio/1.0",
        },
    )
    with urlopen(request, timeout=12) as response:
        raw = response.read(max_chars * 8)

    html = raw.decode("utf-8", errors="ignore")
    parser = PageTextParser()
    parser.feed(html)
    return parser.get_text()[:max_chars].strip()


def load_url_reference_examples(base_path, max_chars):
    if max_chars <= 0:
        return ""

    urls = load_reference_urls(base_path)
    if not urls:
        return ""

    print(f"URL 레퍼런스 {len(urls)}개를 읽는 중입니다...", flush=True)

    blocks = ["## urls"]
    total_chars = 0

    for url in urls:
        if total_chars >= max_chars:
            break

        print(f"- URL 읽는 중: {url}", flush=True)
        try:
            text = fetch_url_text(url, max_chars=min(3000, max_chars - total_chars))
        except (OSError, URLError, TimeoutError) as error:
            text = f"URL을 읽지 못했습니다: {error}"
            print(f"  URL 읽기 실패: {error}", flush=True)

        if not text:
            continue

        print(f"  URL 내용 읽기 완료: {len(text)}자", flush=True)
        blocks.append(f"### {url}\n{text}")
        total_chars += len(text)

    if len(blocks) == 1:
        return ""

    return "\n\n".join(blocks)


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
    print("레퍼런스 자료를 모으는 중입니다...", flush=True)
    examples = load_reference_examples(base_dir)
    if not examples:
        ensure_reference_folders(base_dir)
        return ""

    print("AI가 레퍼런스 스타일을 분석 중입니다...", flush=True)
    prompt = f"""
너는 ShowPark AI Studio의 레퍼런스 분석 에이전트야.
아래 레퍼런스들을 분석해서 앞으로 콘텐츠 에이전트들이 따라야 할 스타일 규칙을 만들어줘.

[분석 기준]
- 톤과 문체
- 후킹 문장 패턴
- 릴스 대본 구조
- 캡션 구조
- 이미지 프롬프트 스타일
- 영상 프롬프트 스타일
- 반복하면 안 되는 표현
- 반드시 따라야 하는 제작 규칙

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
