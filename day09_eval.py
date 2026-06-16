"""
Day09 Async Batch Evaluation Pipeline
======================================
Chạy song song toàn bộ test cases bằng asyncio.Semaphore + asyncio.gather.
Mỗi case được chạy trong thread riêng (để tránh block event loop) và judge
cũng chạy async song song.

Usage:
    python day09_eval.py              # Chạy toàn bộ dataset
    python day09_eval.py --limit 5    # Chỉ chạy 5 câu đầu
    python day09_eval.py --workers 3  # Giới hạn 3 câu song song
"""

import asyncio
import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

# ── Paths ────────────────────────────────────────────────────────
ROOT_PATH = Path(__file__).parent.resolve()
DAY09_PATH = ROOT_PATH / "2A202600846-NguyenHoangThanhTung-Day09"

# Clean sys.path to avoid importing root app.py
sys.path = [p for p in sys.path if p != str(ROOT_PATH) and p != ""]
if str(DAY09_PATH / "src") not in sys.path:
    sys.path.insert(0, str(DAY09_PATH / "src"))

os.chdir(DAY09_PATH)

if "app" in sys.modules:
    del sys.modules["app"]

from app.graph import ShoppingAssistant

os.chdir(ROOT_PATH)
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from engine.day09_judge import Day09Judge

os.chdir(DAY09_PATH)

# ── Config ───────────────────────────────────────────────────────
TEST_FILE = DAY09_PATH / "data" / "test.json"
REPORT_DIR = ROOT_PATH / "reports"


def load_dataset(limit: int | None = None) -> list:
    if not TEST_FILE.exists():
        print(f"❌ Missing {TEST_FILE}.", flush=True)
        return []
    with TEST_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data[:limit] if limit else data


async def evaluate_single_case(
    assistant: ShoppingAssistant,
    judge: Day09Judge,
    test_case: dict,
    semaphore: asyncio.Semaphore,
    index: int,
    total: int,
) -> dict:
    """Evaluate one test case, respecting the semaphore concurrency limit."""
    async with semaphore:
        case_id = test_case.get("id", "?")
        question = test_case["question"]
        print(f"  ▶ [{index}/{total}] {case_id}: {question[:60]}...", flush=True)

        start = time.perf_counter()

        # ShoppingAssistant.ask() is synchronous → run in thread pool
        result = await asyncio.to_thread(assistant.ask, question)
        agent_latency = time.perf_counter() - start

        final_answer = result.get("final_answer", "")
        actual_route = result.get("route", {})
        actual_status = actual_route.get("status", "unknown")

        expected_status = test_case.get("expected_status", "ok")
        expected_contains = test_case.get("expected_contains", [])

        # Judge evaluation (already async)
        judge_start = time.perf_counter()
        judge_result = await judge.evaluate_multi_judge_contains(
            question, final_answer, expected_contains
        )
        judge_latency = time.perf_counter() - judge_start

        status_pass = actual_status == expected_status
        final_score = judge_result["final_score"]
        if not status_pass:
            final_score = min(final_score, 2.0)
        judge_result["final_score"] = final_score

        verdict = "✅" if (status_pass and final_score >= 3.0) else "❌"
        print(
            f"  {verdict} [{index}/{total}] {case_id}: "
            f"Score={final_score}/5.0 | Agent={agent_latency:.1f}s | Judge={judge_latency:.1f}s",
            flush=True,
        )

        return {
            "id": case_id,
            "question": question,
            "expected_route": test_case.get("expected_route", []),
            "expected_status": expected_status,
            "expected_contains": expected_contains,
            "actual_route": actual_route,
            "actual_status": actual_status,
            "status_match": status_pass,
            "final_answer": final_answer,
            "agent_latency": round(agent_latency, 4),
            "judge_latency": round(judge_latency, 4),
            "total_latency": round(agent_latency + judge_latency, 4),
            "judge": judge_result,
            "status": "pass" if (status_pass and final_score >= 3.0) else "fail",
        }


async def run_benchmark(workers: int = 5, limit: int | None = None):
    wall_start = time.perf_counter()

    print("=" * 60, flush=True)
    print("  🚀 Day09 Async Batch Evaluation Pipeline", flush=True)
    print("=" * 60, flush=True)

    dataset = load_dataset(limit)
    if not dataset:
        return
    total = len(dataset)

    print(f"  📦 Loaded {total} test cases", flush=True)
    print(f"  ⚡ Concurrency: {workers} workers (Semaphore)", flush=True)
    print("-" * 60, flush=True)

    assistant = ShoppingAssistant()
    judge = Day09Judge()
    semaphore = asyncio.Semaphore(workers)

    # Fire all tasks concurrently (semaphore controls actual parallelism)
    tasks = [
        evaluate_single_case(assistant, judge, case, semaphore, i + 1, total)
        for i, case in enumerate(dataset)
    ]
    results = await asyncio.gather(*tasks)

    wall_time = time.perf_counter() - wall_start

    # ── Metrics ──────────────────────────────────────────────────
    pass_count = sum(1 for r in results if r["status"] == "pass")
    fail_count = total - pass_count
    avg_score = sum(r["judge"]["final_score"] for r in results) / total
    pass_rate = pass_count / total
    avg_agent_lat = sum(r["agent_latency"] for r in results) / total
    avg_judge_lat = sum(r["judge_latency"] for r in results) / total
    total_agent_lat = sum(r["agent_latency"] for r in results)
    total_judge_lat = sum(r["judge_latency"] for r in results)

    # ── Summary Report ───────────────────────────────────────────
    summary = {
        "metadata": {
            "version": "Day09_ShoppingAssistant",
            "total_cases": total,
            "concurrency_workers": workers,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "metrics": {
            "avg_score": round(avg_score, 2),
            "pass_rate": round(pass_rate, 2),
            "pass_count": pass_count,
            "fail_count": fail_count,
        },
        "performance": {
            "wall_time_seconds": round(wall_time, 2),
            "sequential_time_seconds": round(total_agent_lat + total_judge_lat, 2),
            "speedup_ratio": round((total_agent_lat + total_judge_lat) / wall_time, 2) if wall_time > 0 else 0,
            "avg_agent_latency": round(avg_agent_lat, 2),
            "avg_judge_latency": round(avg_judge_lat, 2),
        },
    }

    REPORT_DIR.mkdir(exist_ok=True)
    with (REPORT_DIR / "day09_eval_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    with (REPORT_DIR / "day09_eval_results.json").open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # ── Print Final Report ───────────────────────────────────────
    print("\n" + "=" * 60, flush=True)
    print("  📊 BENCHMARK RESULTS", flush=True)
    print("=" * 60, flush=True)
    print(f"  Total Cases     : {total}", flush=True)
    print(f"  ✅ Passed        : {pass_count}", flush=True)
    print(f"  ❌ Failed        : {fail_count}", flush=True)
    print(f"  Pass Rate       : {pass_rate*100:.1f}%", flush=True)
    print(f"  Average Score   : {avg_score:.2f} / 5.0", flush=True)
    print("-" * 60, flush=True)
    print(f"  ⏱️  Wall Time     : {wall_time:.1f}s", flush=True)
    print(f"  📈 Sequential    : {total_agent_lat + total_judge_lat:.1f}s (nếu chạy tuần tự)", flush=True)
    print(f"  🚀 Speedup       : {summary['performance']['speedup_ratio']}x nhanh hơn", flush=True)
    print(f"  Avg Agent Lat.  : {avg_agent_lat:.2f}s / case", flush=True)
    print(f"  Avg Judge Lat.  : {avg_judge_lat:.2f}s / case", flush=True)
    print("-" * 60, flush=True)
    print(f"  📁 Reports → {REPORT_DIR}", flush=True)
    print("=" * 60, flush=True)

    # ── Release Gate ─────────────────────────────────────────────
    GATE_THRESHOLD = 3.5
    if avg_score >= GATE_THRESHOLD and pass_rate >= 0.7:
        print(f"\n  🟢 RELEASE GATE: PASSED (avg={avg_score:.2f} ≥ {GATE_THRESHOLD}, rate={pass_rate*100:.0f}% ≥ 70%)", flush=True)
    else:
        print(f"\n  🔴 RELEASE GATE: BLOCKED (avg={avg_score:.2f}, rate={pass_rate*100:.0f}%)", flush=True)


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")

    parser = argparse.ArgumentParser(description="Day09 Async Batch Eval")
    parser.add_argument("--workers", type=int, default=5, help="Số câu chạy song song (default: 5)")
    parser.add_argument("--limit", type=int, default=None, help="Giới hạn số câu (mặc định: toàn bộ)")
    args = parser.parse_args()

    asyncio.run(run_benchmark(workers=args.workers, limit=args.limit))
