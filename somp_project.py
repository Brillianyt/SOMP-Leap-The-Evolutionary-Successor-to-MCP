#!/usr/bin/env python3
"""
SOMP project runner (MVP).

Runs a pipeline defined in JSON:
{
  "exam": {...},
  "welder": {...}
}
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Mapping

from somp_exam import run_exam
from somp_welder import run_welder


def load_json(path: Path) -> Mapping[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SOMP project pipeline (MVP).")
    parser.add_argument(
        "--pipeline",
        required=True,
        help="Path to pipeline JSON configuration.",
    )
    return parser.parse_args()


def run_pipeline(config: Mapping[str, Any]) -> Dict[str, Any]:
    results: Dict[str, Any] = {}

    exam_config = config.get("exam")
    if exam_config:
        results["exam"] = run_exam(
            model=exam_config["model"],
            test_suite=exam_config["test_suite"],
            outputs_path=exam_config.get("outputs"),
            clarity_threshold=exam_config.get("clarity_threshold", 0.9),
            content_threshold=exam_config.get("content_threshold", 0.3),
            max_error_rate=exam_config.get("max_error_rate", 0.05),
            output_json=exam_config.get("output_json", "somp_exam_report.json"),
        )

    welder_config = config.get("welder")
    if welder_config:
        results["welder"] = run_welder(
            input_path=welder_config["input"],
            output_path=welder_config.get("output", "somp_welded.json"),
            strict=welder_config.get("strict", False),
        )

    return results


def main() -> None:
    args = parse_args()
    config = load_json(Path(args.pipeline))
    run_pipeline(config)


if __name__ == "__main__":
    main()
