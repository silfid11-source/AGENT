import csv
import os
from datetime import datetime
from pathlib import Path

from agents import run_showpark_agent_pipeline


DEFAULT_CONTEXT = {
    "content_goal": "신규 고객 유입",
    "topic_text": "사장님이 인스타를 해야 하는 이유",
    "brand_display": "미입력",
    "region_display": "미입력",
    "industry_name": "식당",
    "target": "30~40대 식당 사장님",
    "pain": "음식은 괜찮지만 온라인에서 매장의 차별점이 잘 보이지 않는 상황",
    "visual": "매장 공간, 대표 메뉴, 조리 장면, 손님이 실제로 보는 장면",
    "tone": "현실적이고 직설적인 톤",
    "content_style": "직설형",
    "prompt_preset": "기본형",
    "creativity_mode": "균형형",
    "video_length": "10초",
    "platform": "인스타 릴스",
}
WORKFLOW_INPUT_FIELDS = [
    "enabled",
    "status",
    "content_goal",
    "topic_text",
    "brand_display",
    "region_display",
    "industry_name",
    "target",
    "pain",
    "visual",
    "tone",
    "content_style",
    "prompt_preset",
    "creativity_mode",
    "video_length",
    "platform",
]
WORKFLOW_STATUS_OPTIONS = {"대기", "완료", "오류"}


def normalize_workflow_status(value):
    status = (value or "").strip()
    return status if status in WORKFLOW_STATUS_OPTIONS else "대기"


def clean_filename(value):
    text = (value or "untitled").strip()
    for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
        text = text.replace(char, "_")
    return text.replace(" ", "_")[:80]


def read_workflow_inputs(csv_path):
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    tasks = []
    for row_index, row in enumerate(rows):
        enabled = (row.get("enabled") or "yes").strip().lower()
        if enabled in {"no", "n", "false", "0", "아니오"}:
            continue

        context = DEFAULT_CONTEXT.copy()
        for key in context:
            value = (row.get(key) or "").strip()
            if value:
                context[key] = value

        context["_workflow_row_index"] = row_index
        tasks.append(context)

    return tasks


def update_workflow_input_status(csv_path, row_index, status):
    if row_index is None:
        return

    path = Path(csv_path)
    if not path.exists():
        return

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    if row_index < 0 or row_index >= len(rows):
        return

    for row in rows:
        row["status"] = normalize_workflow_status(row.get("status"))

    rows[row_index]["status"] = normalize_workflow_status(status)

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=WORKFLOW_INPUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def save_workflow_result(context, result, agent_report, output_dir, video_production_package=""):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_name = "_".join(
        [
            clean_filename(context["industry_name"]),
            clean_filename(context["region_display"]),
            clean_filename(context["topic_text"]),
            now,
        ]
    )
    project_folder = Path(output_dir) / project_name
    project_folder.mkdir(parents=True, exist_ok=True)

    result_path = project_folder / "final_result.txt"
    report_path = project_folder / "agent_report.txt"
    summary_path = project_folder / "summary.txt"
    video_package_path = project_folder / "video_production_package.txt"

    result_path.write_text(result, encoding="utf-8")
    report_path.write_text(agent_report, encoding="utf-8")
    if video_production_package:
        video_package_path.write_text(video_production_package, encoding="utf-8")
    summary_path.write_text(
        "\n".join(
            [
                f"콘텐츠 목적: {context['content_goal']}",
                f"주제: {context['topic_text']}",
                f"고객명/브랜드명: {context['brand_display']}",
                f"지역: {context['region_display']}",
                f"업종: {context['industry_name']}",
                f"플랫폼: {context['platform']}",
                f"영상 길이: {context['video_length']}",
                f"생성 시간: {now}",
            ]
        ),
        encoding="utf-8",
    )

    return project_folder


def run_batch_workflow(client, model_name, input_csv, output_dir, limit=None, dry_run=False):
    tasks = read_workflow_inputs(input_csv)
    if limit is not None:
        tasks = tasks[:limit]

    results = []
    for index, context in enumerate(tasks, start=1):
        row_index = context.pop("_workflow_row_index", None)
        if dry_run:
            print(
                f"{index}. 입력 점검: {context['industry_name']} - {context['topic_text']}",
                flush=True,
            )
            results.append(
                {
                    "index": index,
                    "topic": context["topic_text"],
                    "industry": context["industry_name"],
                    "status": "dry_run",
                    "folder": "",
                }
            )
            continue

        print(
            f"{index}. 콘텐츠 생성 중: {context['industry_name']} - {context['topic_text']}",
            flush=True,
        )
        try:
            pipeline = run_showpark_agent_pipeline(client, model_name, context)
            folder = save_workflow_result(
                context,
                pipeline["result"],
                pipeline["agent_report"],
                output_dir,
                pipeline.get("video_production_package", ""),
            )
            update_workflow_input_status(input_csv, row_index, "완료")
            print(f"   저장 완료: {folder}", flush=True)
            results.append(
                {
                    "index": index,
                    "topic": context["topic_text"],
                    "industry": context["industry_name"],
                    "status": "완료",
                    "folder": str(folder),
                }
            )
        except Exception as error:
            update_workflow_input_status(input_csv, row_index, "오류")
            print(f"   오류: {error}", flush=True)
            results.append(
                {
                    "index": index,
                    "topic": context["topic_text"],
                    "industry": context["industry_name"],
                    "status": "오류",
                    "folder": "",
                }
            )

    return results
