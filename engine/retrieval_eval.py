import math
from typing import Dict, List


class RetrievalEvaluator:
    def calculate_hit_rate(self, expected_ids: List[str], retrieved_ids: List[str], top_k: int = 3) -> float:
        expected = set(expected_ids or [])
        retrieved_ids = _dedupe(retrieved_ids or [])
        if not expected:
            return 0.0
        return 1.0 if expected.intersection((retrieved_ids or [])[:top_k]) else 0.0

    def calculate_mrr(self, expected_ids: List[str], retrieved_ids: List[str]) -> float:
        expected = set(expected_ids or [])
        retrieved_ids = _dedupe(retrieved_ids or [])
        if not expected:
            return 0.0
        for index, doc_id in enumerate(retrieved_ids or [], start=1):
            if doc_id in expected:
                return 1.0 / index
        return 0.0

    def calculate_precision_at_k(self, expected_ids: List[str], retrieved_ids: List[str], top_k: int = 3) -> float:
        expected = set(expected_ids or [])
        retrieved_ids = _dedupe(retrieved_ids or [])
        top_retrieved = (retrieved_ids or [])[:top_k]
        if not expected or not top_retrieved:
            return 0.0
        return sum(1 for doc_id in top_retrieved if doc_id in expected) / len(top_retrieved)

    def calculate_ndcg(self, expected_ids: List[str], retrieved_ids: List[str], top_k: int = 3) -> float:
        expected = set(expected_ids or [])
        retrieved_ids = _dedupe(retrieved_ids or [])
        if not expected:
            return 0.0

        dcg = 0.0
        for index, doc_id in enumerate((retrieved_ids or [])[:top_k], start=1):
            if doc_id in expected:
                dcg += 1.0 / math.log2(index + 1)

        ideal_hits = min(len(expected), top_k)
        idcg = sum(1.0 / math.log2(index + 1) for index in range(1, ideal_hits + 1))
        return dcg / idcg if idcg else 0.0

    async def score(self, test_case: Dict, response: Dict, top_k: int = 3) -> Dict:
        expected_ids = test_case.get("expected_retrieval_ids", [])
        retrieved_ids = response.get("retrieved_ids") or response.get("metadata", {}).get("sources", [])
        answer = response.get("answer", "")
        expected_answer = test_case.get("expected_answer", "")

        retrieval = {
            "hit_rate": self.calculate_hit_rate(expected_ids, retrieved_ids, top_k),
            "mrr": self.calculate_mrr(expected_ids, retrieved_ids),
            "precision_at_k": self.calculate_precision_at_k(expected_ids, retrieved_ids, top_k),
            "ndcg": self.calculate_ndcg(expected_ids, retrieved_ids, top_k),
            "expected_ids": expected_ids,
            "retrieved_ids": retrieved_ids,
        }

        expected_terms = _content_terms(expected_answer)
        answer_terms = _content_terms(answer)
        overlap = len(expected_terms.intersection(answer_terms))
        relevancy = overlap / max(len(expected_terms), 1)
        faithfulness = 1.0 if retrieval["hit_rate"] and response.get("contexts") else 0.35

        return {
            "faithfulness": round(min(faithfulness, 1.0), 3),
            "relevancy": round(min(relevancy, 1.0), 3),
            "retrieval": retrieval,
        }

    async def evaluate_batch(self, dataset: List[Dict]) -> Dict:
        if not dataset:
            return {"avg_hit_rate": 0.0, "avg_mrr": 0.0, "avg_precision_at_k": 0.0, "avg_ndcg": 0.0}

        hit_rates = []
        mrrs = []
        precisions = []
        ndcgs = []
        for item in dataset:
            expected_ids = item.get("expected_retrieval_ids", [])
            retrieved_ids = item.get("retrieved_ids", [])
            hit_rates.append(self.calculate_hit_rate(expected_ids, retrieved_ids))
            mrrs.append(self.calculate_mrr(expected_ids, retrieved_ids))
            precisions.append(self.calculate_precision_at_k(expected_ids, retrieved_ids))
            ndcgs.append(self.calculate_ndcg(expected_ids, retrieved_ids))

        count = len(dataset)
        return {
            "avg_hit_rate": sum(hit_rates) / count,
            "avg_mrr": sum(mrrs) / count,
            "avg_precision_at_k": sum(precisions) / count,
            "avg_ndcg": sum(ndcgs) / count,
        }


def _content_terms(text: str) -> set:
    stopwords = {
        "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with", "is",
        "are", "be", "should", "what", "why", "how", "does", "do", "it", "that",
    }
    tokens = []
    for raw in (text or "").lower().replace("-", " ").split():
        token = "".join(ch for ch in raw if ch.isalnum())
        if len(token) > 2 and token not in stopwords:
            tokens.append(token)
    return set(tokens)


def _dedupe(values: List[str]) -> List[str]:
    deduped = []
    seen = set()
    for value in values:
        if value in seen:
            continue
        deduped.append(value)
        seen.add(value)
    return deduped
