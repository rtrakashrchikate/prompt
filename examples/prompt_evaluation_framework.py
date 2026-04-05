"""
Prompt Evaluation Framework
Author: Rehan Malik

Framework for systematic prompt testing and optimization.
Used to evaluate and compare prompt variants before production deployment.
"""

import json
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class TestCase:
    input_text: str
    expected_output: str
    category: str = "general"
    difficulty: str = "medium"  # easy, medium, hard


@dataclass
class EvalResult:
    test_case: TestCase
    actual_output: str
    score: float  # 0-1
    latency_ms: float
    token_count: int
    passed: bool


class PromptEvaluator:
    """Evaluate prompts against test suites with multiple metrics."""

    def __init__(self):
        self.test_suites: dict[str, list[TestCase]] = {}
        self.results: dict[str, list[EvalResult]] = {}

    def add_test_suite(self, name: str, cases: list[TestCase]):
        self.test_suites[name] = cases

    def evaluate(self, prompt_name: str, prompt_fn: Callable,
                 suite_name: str, scorer: Callable) -> dict:
        """Run evaluation of a prompt against a test suite."""
        cases = self.test_suites.get(suite_name, [])
        results = []

        for case in cases:
            output = prompt_fn(case.input_text)
            score = scorer(case.expected_output, output)
            result = EvalResult(
                test_case=case,
                actual_output=output,
                score=score,
                latency_ms=0,  # would be measured in production
                token_count=len(output.split()),
                passed=score >= 0.8
            )
            results.append(result)

        self.results[prompt_name] = results
        return self._summarize(prompt_name, results)

    def _summarize(self, name: str, results: list[EvalResult]) -> dict:
        scores = [r.score for r in results]
        return {
            "prompt": name,
            "total_cases": len(results),
            "passed": sum(1 for r in results if r.passed),
            "failed": sum(1 for r in results if not r.passed),
            "avg_score": round(sum(scores) / len(scores), 4) if scores else 0,
            "min_score": round(min(scores), 4) if scores else 0,
            "max_score": round(max(scores), 4) if scores else 0,
        }

    def compare(self, prompt_names: list[str]) -> str:
        """Compare multiple prompts side by side."""
        lines = ["\nPrompt Comparison:", "-" * 50]
        for name in prompt_names:
            if name in self.results:
                summary = self._summarize(name, self.results[name])
                lines.append(
                    f"  {name}: avg={summary['avg_score']:.3f} "
                    f"pass={summary['passed']}/{summary['total_cases']}"
                )
        return "\n".join(lines)


if __name__ == "__main__":
    evaluator = PromptEvaluator()

    evaluator.add_test_suite("classification", [
        TestCase("My payment failed", "billing_issue", "billing"),
        TestCase("How do I export data?", "feature_question", "support"),
        TestCase("Your app is amazing!", "feedback_positive", "feedback"),
    ])

    def simple_prompt(text):
        return "billing_issue" if "payment" in text else "feature_question"

    def exact_match_scorer(expected, actual):
        return 1.0 if expected.strip() == actual.strip() else 0.0

    result = evaluator.evaluate("v1_simple", simple_prompt, "classification", exact_match_scorer)
    print(json.dumps(result, indent=2))
