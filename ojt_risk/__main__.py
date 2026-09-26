import argparse
import json
import sys
from pathlib import Path

from .engine import DataError, analyze, load_data


def main():
    parser = argparse.ArgumentParser(description="Analyze OJT eligibility from five CSV tables")
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--evaluation-term", required=True)
    parser.add_argument("--target-term", required=True)
    parser.add_argument("--output", type=Path, default=Path("output/report.json"))
    args = parser.parse_args()
    try:
        tables, warnings = load_data(args.data)
        report = analyze(tables, args.evaluation_term, args.target_term)
    except (OSError, UnicodeError, DataError) as exc:
        parser.exit(2, f"Data error: {exc}\n")
    report["warnings"] = warnings
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
    print(f"Report: {args.output.resolve()}")


if __name__ == "__main__":
    main()
