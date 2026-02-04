#!/usr/bin/env python3
"""
SOMP Auto-Welder (MVP).

Takes raw model output (text or JSON) and normalizes it into:
JSON{universal + specific} for downstream agent compatibility.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional


@dataclass
class UniversalLayer:
    intent: str
    summary: str
    confidence: float


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def infer_universal(text: str) -> UniversalLayer:
    summary = text.strip() or "无摘要"
    return UniversalLayer(intent="unspecified", summary=summary, confidence=0.5)


def normalize_payload(payload: Any, strict: bool = False) -> Dict[str, Any]:
    if isinstance(payload, str):
        universal = infer_universal(payload)
        return {
            "universal": {
                "intent": universal.intent,
                "summary": universal.summary,
                "confidence": universal.confidence,
            },
            "specific": {"raw_text": payload},
        }

    if not isinstance(payload, Mapping):
        raise ValueError("Input payload must be JSON object or string.")

    universal = payload.get("universal")
    specific = payload.get("specific", {})

    if not isinstance(universal, Mapping):
        if strict:
            raise ValueError("Missing universal layer.")
        universal = infer_universal(json.dumps(payload, ensure_ascii=False))

    intent = str(universal.get("intent", "unspecified"))
    summary = str(universal.get("summary", "无摘要"))
    confidence = clamp(float(universal.get("confidence", 0.5)))

    if strict and (not intent or not summary):
        raise ValueError("Universal layer missing required fields.")

    return {
        "universal": {
            "intent": intent,
            "summary": summary,
            "confidence": confidence,
        },
        "specific": specific,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SOMP Auto-Welder (MVP).")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to input JSON or raw text file.",
    )
    parser.add_argument(
        "--output",
        default="somp_welded.json",
        help="Path to write normalized SOMP output.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if universal layer is missing or invalid.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    raw_text = input_path.read_text(encoding="utf-8").strip()

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        payload = raw_text

    normalized = normalize_payload(payload, strict=args.strict)
    write_json(Path(args.output), normalized)
    print(json.dumps(normalized, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
