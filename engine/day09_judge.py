import os
from typing import Any, Dict, List, Tuple
from engine.llm_judge import LLMJudge
from engine.llm_client import LLMClient

class Day09Judge(LLMJudge):
    def __init__(self, model: str = "online-consensus"):
        super().__init__(model)
        # Tweak the semantic prompt for checking a list of keywords/meanings
        self.rubrics = {
            "information_coverage": "1-5: answer contains the semantic meaning of all required expected_contains elements.",
            "correct_status": "Status matches expected status."
        }

    async def evaluate_multi_judge_contains(self, question: str, answer: str, expected_contains: List[str]) -> Dict[str, Any]:
        if not expected_contains:
            return {
                "final_score": 5.0,
                "agreement_rate": 1.0,
                "individual_scores": {"judge_strict": 5.0, "judge_semantic": 5.0},
                "resolution": "auto_pass_no_expected_contains",
                "rubrics": self.rubrics,
                "reasoning": {"judge_strict": "No constraints", "judge_semantic": "No constraints"},
            }

        contains_str = "\n".join([f"- {item}" for item in expected_contains])
        
        score_a, reason_a = await self._strict_judge_contains(question, answer, contains_str)
        score_b, reason_b = await self._semantic_judge_contains(question, answer, contains_str)
        diff = abs(score_a - score_b)

        if diff > 1.0:
            final_score = min(score_a, score_b) + 0.5
            resolution = "conflict_resolved_conservative"
        else:
            final_score = (score_a + score_b) / 2
            resolution = "average"

        agreement_rate = 1.0 if diff == 0 else max(0.0, 1.0 - (diff / 4.0))

        return {
            "final_score": round(final_score, 2),
            "agreement_rate": round(agreement_rate, 3),
            "individual_scores": {
                "judge_strict": score_a,
                "judge_semantic": score_b,
            },
            "resolution": resolution,
            "rubrics": self.rubrics,
            "reasoning": {
                "judge_strict": reason_a,
                "judge_semantic": reason_b,
            },
        }

    async def _strict_judge_contains(self, question: str, answer: str, contains_str: str) -> Tuple[float, str]:
        system_prompt = (
            "You are a strict technical judge. "
            "You must evaluate if the Answer contains ALL the exact required elements provided in the Expected Contains list. "
            "Return your evaluation strictly in the format: SCORE|REASONING\n"
            "SCORE must be a float between 1.0 and 5.0. 5.0 means all elements are strictly found, 1.0 means completely missing."
        )
        prompt = f"Question: {question}\nExpected Contains:\n{contains_str}\n\nAnswer: {answer}\nEvaluate:"
        
        response = await self.strict_client.generate_response(prompt, system_prompt=system_prompt, temperature=0.1)
        return self._parse_llm_response(response)

    async def _semantic_judge_contains(self, question: str, answer: str, contains_str: str) -> Tuple[float, str]:
        system_prompt = (
            "You are a semantic evaluator. "
            "Evaluate if the Answer expresses the semantic meaning of the items in the Expected Contains list. "
            "Ignore exact wording, focus on the presence of the meaning. "
            "Return your evaluation strictly in the format: SCORE|REASONING\n"
            "SCORE must be a float between 1.0 and 5.0."
        )
        prompt = f"Question: {question}\nExpected Contains:\n{contains_str}\n\nAnswer: {answer}\nEvaluate:"
        
        response = await self.semantic_client.generate_response(prompt, system_prompt=system_prompt, temperature=0.3)
        return self._parse_llm_response(response)
