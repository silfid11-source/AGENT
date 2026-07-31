import argparse
import os

from reference_analyzer import analyze_references, ensure_reference_folders
from workflows import run_batch_workflow


def load_env_file(path=".env"):
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main():
    parser = argparse.ArgumentParser(description="ShowPark AI Studio 자동 워크플로우 실행")
    parser.add_argument("--input", default="workflow_inputs.csv", help="자동화 입력 CSV 파일")
    parser.add_argument("--output", default="workflow_outputs", help="결과 저장 폴더")
    parser.add_argument("--model", default="gpt-5-mini", help="사용할 OpenAI 모델")
    parser.add_argument("--limit", type=int, default=None, help="앞에서부터 실행할 작업 수")
    parser.add_argument("--dry-run", action="store_true", help="API 호출 없이 입력만 점검")
    parser.add_argument("--references", default="references", help="레퍼런스 자료 폴더")
    parser.add_argument(
        "--analyze-references",
        action="store_true",
        help="자동화 실행 전에 레퍼런스 자료를 분석해서 규칙을 생성",
    )
    args = parser.parse_args()

    ensure_reference_folders(args.references)
    load_env_file()

    client = None
    if not args.dry_run:
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(".env 파일에서 OPENAI_API_KEY를 찾을 수 없습니다.")
        client = OpenAI(api_key=api_key)

    if args.analyze_references:
        if args.dry_run:
            print("레퍼런스 폴더 점검 완료: API 호출 없이 분석은 건너뜁니다.")
        else:
            rules = analyze_references(
                client=client,
                model_name=args.model,
                base_dir=args.references,
            )
            if rules:
                print("레퍼런스 분석 완료: reference_rules.md")
            else:
                print("레퍼런스 파일이 없어 분석을 건너뜁니다.")

    results = run_batch_workflow(
        client=client,
        model_name=args.model,
        input_csv=args.input,
        output_dir=args.output,
        limit=args.limit,
        dry_run=args.dry_run,
    )

    print("ShowPark 자동 워크플로우 결과")
    print("-" * 32)
    for item in results:
        print(f"{item['index']}. [{item['status']}] {item['industry']} - {item['topic']}")
        if item["folder"]:
            print(f"   저장 위치: {item['folder']}")


if __name__ == "__main__":
    main()
