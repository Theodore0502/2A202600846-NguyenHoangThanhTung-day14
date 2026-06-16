import asyncio
import time
from typing import Dict, List


class BenchmarkRunner:
    def __init__(self, agent, evaluator, judge):
        self.agent = agent
        self.evaluator = evaluator
        self.judge = judge

    async def run_single_test(self, test_case: Dict, index: int, total: int) -> Dict:
        start_time = time.perf_counter()
        response = await self.agent.query(test_case["question"])
        latency = time.perf_counter() - start_time

        ragas_scores = await self.evaluator.score(test_case, response)
        
        judge_start = time.perf_counter()
        judge_result = await self.judge.evaluate_multi_judge(
            test_case["question"],
            response["answer"],
            test_case["expected_answer"],
        )
        judge_latency = time.perf_counter() - judge_start
        
        tokens_used = response.get("metadata", {}).get("tokens_used", 0)
        cost_usd = response.get("metadata", {}).get("estimated_cost_usd", 0.0)
        final_score = judge_result["final_score"]
        status = "fail" if final_score < 3.0 else "pass"
        
        verdict = "✅" if status == "pass" else "❌"
        print(f"  {verdict} [{index}/{total}] Q: {test_case['question'][:40]}... | Score: {final_score}/5.0 | Tokens: {tokens_used} | Cost: ${cost_usd:.6f} | Agent Lat: {latency:.2f}s | Judge Lat: {judge_latency:.2f}s", flush=True)

        return {
            "id": test_case.get("metadata", {}).get("source_doc_id", "unknown"),
            "difficulty": test_case.get("metadata", {}).get("difficulty", "unknown"),
            "type": test_case.get("metadata", {}).get("type", "unknown"),
            "test_case": test_case["question"],
            "expected_answer": test_case.get("expected_answer", ""),
            "expected_retrieval_ids": test_case.get("expected_retrieval_ids", []),
            "agent_response": response["answer"],
            "retrieved_ids": response.get("retrieved_ids", []),
            "latency": round(latency, 4),
            "tokens_used": tokens_used,
            "estimated_cost_usd": cost_usd,
            "ragas": ragas_scores,
            "judge": judge_result,
            "status": status,
        }

    async def run_all(self, dataset: List[Dict], batch_size: int = 10) -> List[Dict]:
        results = []
        total = len(dataset)
        for index in range(0, total, batch_size):
            batch = dataset[index:index + batch_size]
            print(f"\n  [Batch {index//batch_size + 1}] Processing {len(batch)} cases concurrently...", flush=True)
            batch_results = await asyncio.gather(*(self.run_single_test(case, index + i + 1, total) for i, case in enumerate(batch)))
            results.extend(batch_results)
        return results
