import json
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
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


class PageMetadataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title_parts = []
        self.meta = {}
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self.in_title = True
            return

        if tag != "meta":
            return

        key = attrs.get("property") or attrs.get("name")
        content = attrs.get("content")
        if key and content:
            self.meta[key.lower()] = unescape(content.strip())

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            text = " ".join(data.split())
            if text:
                self.title_parts.append(text)

    def get_metadata_text(self):
        lines = []
        title = self.meta.get("og:title") or " ".join(self.title_parts).strip()
        description = self.meta.get("og:description") or self.meta.get("description")
        site_name = self.meta.get("og:site_name")

        if site_name:
            lines.append(f"사이트: {site_name}")
        if title:
            lines.append(f"제목: {title}")
        if description:
            lines.append(f"설명: {description}")

        return "\n".join(lines).strip()


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


def fetch_url_html(url, max_bytes=240000):
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    )
    with urlopen(request, timeout=12) as response:
        raw = response.read(max_bytes)

    return raw.decode("utf-8", errors="ignore")


def get_youtube_video_id(url):
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path_parts = [part for part in parsed.path.split("/") if part]

    if "youtu.be" in host and path_parts:
        return path_parts[0]

    if "youtube.com" not in host:
        return ""

    query_id = parse_qs(parsed.query).get("v", [""])[0]
    if query_id:
        return query_id

    if len(path_parts) >= 2 and path_parts[0] in {"shorts", "embed", "live"}:
        return path_parts[1]

    return ""


def extract_json_after_marker(text, marker):
    start = text.find(marker)
    if start == -1:
        return None

    brace_start = text.find("{", start + len(marker))
    if brace_start == -1:
        return None

    depth = 0
    in_string = False
    escaped = False
    for index in range(brace_start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[brace_start:index + 1]

    return None


def parse_youtube_player_response(html):
    for marker in ["ytInitialPlayerResponse =", "ytInitialPlayerResponse = "]:
        payload = extract_json_after_marker(html, marker)
        if not payload:
            continue

        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            continue

    return {}


def strip_xml_text(xml_text):
    parser = PageTextParser()
    parser.feed(xml_text)
    return parser.get_text()


def fetch_youtube_transcript(player_response, max_chars=1800):
    captions = (
        player_response
        .get("captions", {})
        .get("playerCaptionsTracklistRenderer", {})
        .get("captionTracks", [])
    )
    if not captions:
        return ""

    preferred_track = None
    for language_code in ["ko", "en"]:
        preferred_track = next(
            (
                track
                for track in captions
                if track.get("languageCode", "").lower().startswith(language_code)
            ),
            None,
        )
        if preferred_track:
            break

    track = preferred_track or captions[0]
    base_url = track.get("baseUrl")
    if not base_url:
        return ""

    request = Request(
        base_url,
        headers={
            "User-Agent": "Mozilla/5.0 ShowParkAIStudio/1.0",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    )
    with urlopen(request, timeout=12) as response:
        raw = response.read(max_chars * 8)

    transcript = strip_xml_text(raw.decode("utf-8", errors="ignore"))
    return transcript[:max_chars].strip()


def fetch_youtube_oembed(url):
    query = urlencode({"url": url, "format": "json"})
    request = Request(
        f"https://www.youtube.com/oembed?{query}",
        headers={
            "User-Agent": "Mozilla/5.0 ShowParkAIStudio/1.0",
            "Accept": "application/json",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    )
    with urlopen(request, timeout=12) as response:
        raw = response.read(60000)

    try:
        return json.loads(raw.decode("utf-8", errors="ignore"))
    except json.JSONDecodeError:
        return {}


def extract_youtube_reference_text(url, html, max_chars):
    player_response = parse_youtube_player_response(html)
    video_details = player_response.get("videoDetails", {})
    lines = [f"URL: {url}", "유형: YouTube/Shorts 영상 레퍼런스"]
    metadata_parser = PageMetadataParser()
    metadata_parser.feed(html)

    title = video_details.get("title")
    author = video_details.get("author")
    short_description = video_details.get("shortDescription")
    keywords = video_details.get("keywords") or []

    title = title or metadata_parser.meta.get("og:title") or " ".join(metadata_parser.title_parts).strip()
    short_description = (
        short_description
        or metadata_parser.meta.get("og:description")
        or metadata_parser.meta.get("description")
    )

    if not title:
        try:
            oembed = fetch_youtube_oembed(url)
        except (OSError, URLError, TimeoutError):
            oembed = {}

        title = oembed.get("title") or title
        author = oembed.get("author_name") or author

    if title:
        lines.append(f"제목: {title}")
    if author:
        lines.append(f"채널: {author}")
    if short_description:
        lines.append(f"설명: {short_description}")
    if keywords:
        lines.append(f"키워드: {', '.join(keywords[:20])}")

    try:
        transcript = fetch_youtube_transcript(player_response)
    except (OSError, URLError, TimeoutError):
        transcript = ""

    if transcript:
        lines.append(f"자막/스크립트: {transcript}")
    else:
        lines.append("자막/스크립트: 공개 자막을 찾지 못했습니다. 제목, 설명, 키워드 중심으로 분석합니다.")

    return "\n".join(lines)[:max_chars].strip()


def fetch_url_text(url, max_chars=3000):
    html = fetch_url_html(url)

    if get_youtube_video_id(url):
        youtube_text = extract_youtube_reference_text(url, html, max_chars)
        if youtube_text:
            return youtube_text

    metadata_parser = PageMetadataParser()
    metadata_parser.feed(html)
    metadata_text = metadata_parser.get_metadata_text()

    parser = PageTextParser()
    parser.feed(html)
    page_text = parser.get_text()

    combined = "\n\n".join(
        part
        for part in [metadata_text, page_text]
        if part
    )
    return combined[:max_chars].strip()


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
