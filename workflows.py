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
    for row in rows:
        enabled = (row.get("enabled") or "yes").strip().lower()
        if enabled in {"no", "n", "false", "0", "아니오"}:
            continue

        context = DEFAULT_CONTEXT.copy()
        for key in context:
            value = (row.get(key) or "").strip()
            if value:
                context[key] = value

        tasks.append(context)

    return tasks


def save_workflow_result(context, result, agent_report, output_dir):
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

    result_path.write_text(result, encoding="utf-8")
    report_path.write_text(agent_report, encoding="utf-8")
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
        if dry_run:
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

        pipeline = run_showpark_agent_pipeline(client, model_name, context)
        folder = save_workflow_result(
            context,
            pipeline["result"],
            pipeline["agent_report"],
            output_dir,
        )
        results.append(
            {
                "index": index,
                "topic": context["topic_text"],
                "industry": context["industry_name"],
                "status": "saved",
                "folder": str(folder),
            }
        )

    return results

