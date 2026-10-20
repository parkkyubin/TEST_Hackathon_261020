"""CLI (TD3): python -m tripmate --input sample_input.json --format text|json [--no-llm]"""
import argparse
import json
import os
import sys

from .pipeline import run, to_text

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m tripmate", description="트립메이트 — 여행 일정 변경 대응")
    ap.add_argument("--input", default=os.path.join(ROOT, "sample_input.json"))
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--no-llm", action="store_true", help="LLM 요약 생략")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        with open(a.input, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        print(f"입력 파일을 찾을 수 없습니다: {a.input}")
        return 2
    except json.JSONDecodeError as e:
        print(f"입력 JSON 형식 오류: {e}")
        return 2
    res = run(data, use_llm=not a.no_llm)
    if a.format == "json":
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(to_text(res))
    return 0 if res.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())
