import asyncio
import json
import os
import time
from pathlib import Path

from agent.main_agent import MainAgent
from engine.llm_judge import LLMJudge
from engine.retrieval_eval import RetrievalEvaluator
from engine.runner import BenchmarkRunner

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


DATASET_PATH = Path("data/golden_set.jsonl")
REPORT_DIR = Path("reports")


def load_dataset():
    if not DATASET_PATH.exists():
        print("Missing data/golden_set.jsonl. Run: python data/synthetic_gen.py")
        return []

    with DATASET_PATH.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def build_summary(agent_version: str, results):
    total = len(results)
    if total == 0:
        return {
            "metadata": {"version": agent_version, "total": 0, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")},
            "metrics": {},
            "release_gate": {"decision": "BLOCK", "reasons": ["empty_dataset"]},
        }

    avg = lambda values: sum(values) / total
    metrics = {
        "avg_score": avg([r["judge"]["final_score"] for r in results]),
        "pass_rate": avg([1.0 if r["status"] == "pass" else 0.0 for r in results]),
        "hit_rate": avg([r["ragas"]["retrieval"]["hit_rate"] for r in results]),
        "mrr": avg([r["ragas"]["retrieval"]["mrr"] for r in results]),
        "precision_at_k": avg([r["ragas"]["retrieval"]["precision_at_k"] for r in results]),
        "ndcg": avg([r["ragas"]["retrieval"]["ndcg"] for r in results]),
        "faithfulness": avg([r["ragas"]["faithfulness"] for r in results]),
        "relevancy": avg([r["ragas"]["relevancy"] for r in results]),
        "agreement_rate": avg([r["judge"]["agreement_rate"] for r in results]),
        "avg_latency_seconds": avg([r["latency"] for r in results]),
        "total_tokens": sum(r["tokens_used"] for r in results),
        "total_estimated_cost_usd": round(sum(r["estimated_cost_usd"] for r in results), 6),
    }

    reasons = []
    if metrics["avg_score"] < 4.0:
        reasons.append("avg_score_below_4")
    if metrics["hit_rate"] < 0.9:
        reasons.append("hit_rate_below_90_percent")
    if metrics["agreement_rate"] < 0.7:
        reasons.append("agreement_rate_below_70_percent")
    if metrics["avg_latency_seconds"] > 2.4:
        reasons.append("latency_too_high_for_50_cases_under_2_minutes")

    return {
        "metadata": {
            "version": agent_version,
            "total": total,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "uses_multi_judge": True,
            "uses_retrieval_metrics": True,
        },
        "metrics": {key: round(value, 6) if isinstance(value, float) else value for key, value in metrics.items()},
        "release_gate": {
            "decision": "APPROVE" if not reasons else "BLOCK",
            "reasons": reasons,
            "thresholds": {
                "avg_score": ">= 4.0",
                "hit_rate": ">= 0.9",
                "agreement_rate": ">= 0.7",
                "avg_latency_seconds": "<= 2.4",
            },
        },
    }


async def run_benchmark_with_results(agent_version: str):
    print(f"Starting benchmark for {agent_version}...")
    dataset = load_dataset()
    if not dataset:
        return [], build_summary(agent_version, [])

    agent_mode = "baseline" if "Base" in agent_version else "optimized"
    runner = BenchmarkRunner(
        MainAgent(version=agent_mode),
        RetrievalEvaluator(),
        LLMJudge(),
    )
    # Giảm batch size xuống 3 để tránh lỗi 429 Rate Limit từ DashScope
    results = await runner.run_all(dataset, batch_size=3)
    return results, build_summary(agent_version, results)


async def main():
    if load_dotenv:
        load_dotenv()

    v1_results, v1_summary = await run_benchmark_with_results("Agent_V1_Base")
    v2_results, v2_summary = await run_benchmark_with_results("Agent_V2_Optimized")

    delta = v2_summary["metrics"].get("avg_score", 0) - v1_summary["metrics"].get("avg_score", 0)
    v2_summary["regression"] = {
        "baseline_version": v1_summary["metadata"]["version"],
        "candidate_version": v2_summary["metadata"]["version"],
        "avg_score_delta": round(delta, 6),
        "quality_regressed": delta < 0,
    }
    if delta < 0:
        v2_summary["release_gate"]["decision"] = "BLOCK"
        v2_summary["release_gate"]["reasons"].append("quality_regressed_vs_baseline")

    REPORT_DIR.mkdir(exist_ok=True)
    with (REPORT_DIR / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(v2_summary, f, ensure_ascii=False, indent=2)
    with (REPORT_DIR / "benchmark_results.json").open("w", encoding="utf-8") as f:
        json.dump(v2_results, f, ensure_ascii=False, indent=2)
    with (REPORT_DIR / "baseline_results.json").open("w", encoding="utf-8") as f:
        json.dump({"summary": v1_summary, "results": v1_results}, f, ensure_ascii=False, indent=2)

    print("\n--- Regression Summary ---")
    print(f"V1 avg score: {v1_summary['metrics'].get('avg_score', 0):.2f}")
    print(f"V2 avg score: {v2_summary['metrics'].get('avg_score', 0):.2f}")
    print(f"Delta: {delta:+.2f}")
    print(f"Release gate: {v2_summary['release_gate']['decision']}")
    print(f"Reports written to {REPORT_DIR}")


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    asyncio.run(main())
