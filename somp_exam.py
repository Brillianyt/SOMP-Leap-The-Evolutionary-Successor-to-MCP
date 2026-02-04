#!/usr/bin/env python3
"""
SOMP language exam (MVP).

This is a local, non-networked evaluator that simulates:
1) model output generation (via mock outputs)
2) paraphrase consistency (stubbed "Kimi" rephrasing)
3) basic content alignment (optional expected answers)
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Mapping, Optional


@dataclass
class CaseResult:
    case_id: str
    prompt: str
    expected: Optional[str]
    model_output: str
    paraphrase_output: str
    clarity_score: float
    content_score: float
    passed: bool


def load_json(path: Path) -> Mapping:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_text(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def tokenize(text: str) -> List[str]:
    text = normalize_text(text)
    tokens: List[str] = []
    buffer: List[str] = []
    for char in text:
        if "\u4e00" <= char <= "\u9fff":
            if buffer:
                tokens.append("".join(buffer))
                buffer = []
            tokens.append(char)
        elif char.isalnum():
            buffer.append(char)
        else:
            if buffer:
                tokens.append("".join(buffer))
                buffer = []
    if buffer:
        tokens.append("".join(buffer))
    return tokens


def jaccard_similarity(left: str, right: str) -> float:
    left_tokens = set(tokenize(left))
    right_tokens = set(tokenize(right))
    if not left_tokens and not right_tokens:
        return 1.0
    intersection = left_tokens & right_tokens
    union = left_tokens | right_tokens
    if not union:
        return 0.0
    return len(intersection) / len(union)


def paraphrase_stub(text: str) -> str:
    """Local paraphrase placeholder for Kimi-style rephrasing."""
    text = normalize_text(text)
    text = re.sub(r"[，。！？]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def evaluate_cases(
    cases: Iterable[Mapping[str, str]],
    outputs: Mapping[str, str],
    clarity_threshold: float,
    content_threshold: float,
) -> List[CaseResult]:
    results: List[CaseResult] = []
    for case in cases:
        case_id = case["id"]
        prompt = case["prompt"]
        expected = case.get("expected")
        model_output = outputs.get(case_id, "")
        paraphrase_output = paraphrase_stub(model_output)
        clarity_score = jaccard_similarity(model_output, paraphrase_output)
        content_score = (
            jaccard_similarity(model_output, expected) if expected else 1.0
        )
        passed = (
            clarity_score >= clarity_threshold
            and content_score >= content_threshold
        )
        results.append(
            CaseResult(
                case_id=case_id,
                prompt=prompt,
                expected=expected,
                model_output=model_output,
                paraphrase_output=paraphrase_output,
                clarity_score=clarity_score,
                content_score=content_score,
                passed=passed,
            )
        )
    return results


def build_summary(results: List[CaseResult], max_error_rate: float) -> Mapping:
    total = len(results)
    passed = sum(1 for result in results if result.passed)
    error_rate = 1.0 - (passed / total if total else 0.0)
    status = "pass" if error_rate <= max_error_rate else "fail"
    return {
        "total": total,
        "passed": passed,
        "error_rate": round(error_rate, 4),
        "max_error_rate": max_error_rate,
        "status": status,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SOMP language exam (MVP).")
    parser.add_argument("--model", required=True, help="Model name under test.")
    parser.add_argument(
        "--test-suite",
        required=True,
        help="Name of the test suite in data/test_suites.",
    )
    parser.add_argument(
        "--outputs",
        help="Path to JSON file with model outputs.",
    )
    parser.add_argument(
        "--clarity-threshold",
        type=float,
        default=0.9,
        help="Minimum paraphrase consistency score per case.",
    )
    parser.add_argument(
        "--content-threshold",
        type=float,
        default=0.3,
        help="Minimum content alignment score per case.",
    )
    parser.add_argument(
        "--max-error-rate",
        type=float,
        default=0.05,
        help="Maximum allowable error rate for the test suite.",
    )
    parser.add_argument(
        "--output-json",
        default="somp_exam_report.json",
        help="Path to write the exam report JSON.",
    )
    return parser.parse_args()


def run_exam(
    model: str,
    test_suite: str,
    outputs_path: Optional[str],
    clarity_threshold: float,
    content_threshold: float,
    max_error_rate: float,
    output_json: str,
) -> Mapping[str, object]:
    suite_path = Path("data/test_suites") / f"{test_suite}.json"
    suite = load_json(suite_path)
    cases = suite.get("cases", [])
    if outputs_path:
        outputs = load_json(Path(outputs_path))
    else:
        sample_path = Path("data/sample_outputs") / f"{test_suite}.json"
        outputs = load_json(sample_path)

    results = evaluate_cases(
        cases=cases,
        outputs=outputs,
        clarity_threshold=clarity_threshold,
        content_threshold=content_threshold,
    )
    summary = build_summary(results, max_error_rate)

    report = {
        "model": model,
        "suite": test_suite,
        "summary": summary,
        "cases": [
            {
                "id": result.case_id,
                "prompt": result.prompt,
                "expected": result.expected,
                "model_output": result.model_output,
                "paraphrase_output": result.paraphrase_output,
                "clarity_score": round(result.clarity_score, 4),
                "content_score": round(result.content_score, 4),
                "passed": result.passed,
            }
            for result in results
        ],
    }

    output_path = Path(output_json)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)

    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    return report


def main() -> None:
    args = parse_args()
    run_exam(
        model=args.model,
        test_suite=args.test_suite,
        outputs_path=args.outputs,
        clarity_threshold=args.clarity_threshold,
        content_threshold=args.content_threshold,
        max_error_rate=args.max_error_rate,
        output_json=args.output_json,
    )


if __name__ == "__main__":
    main()
