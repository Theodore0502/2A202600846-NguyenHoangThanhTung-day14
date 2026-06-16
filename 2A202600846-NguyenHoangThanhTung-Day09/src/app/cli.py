from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.graph import ShoppingAssistant


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Student scaffold CLI.")
    parser.add_argument("--question", help="Run one question through the graph.")
    parser.add_argument("--test-file", default="data/test.json")
    parser.add_argument("--trace-file", default=None)
    parser.add_argument("--batch", action="store_true")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild Chroma index")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    assistant = ShoppingAssistant()

    if args.batch:
        test_file = Path(args.test_file)
        output_dir = Path("outputs")
        summary = assistant.run_batch(test_file, output_dir, rebuild_index=args.rebuild)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    elif args.question:
        trace_path = Path(args.trace_file) if args.trace_file else None
        result = assistant.ask(args.question, trace_file=trace_path, rebuild_index=args.rebuild)
        print("\n--- FINAL ANSWER ---\n")
        print(result.get("final_answer", ""))
        print("\n--------------------\n")
    else:
        print("Please provide --question or --batch")


if __name__ == "__main__":
    main()
