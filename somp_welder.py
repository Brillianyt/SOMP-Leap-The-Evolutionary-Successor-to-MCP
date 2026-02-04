#!/usr/bin/env python3
"""
SOMP Auto-Welder (MVP).

Takes raw model output (text or JSON) and normalizes it into:
JSON{universal + specific} for downstream agent compatibility.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from somp_schema import normalize_universal


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def normalize_payload(payload: Any, strict: bool = False) -> Dict[str, Any]:
    if isinstance(payload, str):
        return {
            "universal": normalize_universal(None, payload, strict),
            "specific": {"raw_text": payload},
        }

    if not isinstance(payload, Mapping):
        raise ValueError("Input payload must be JSON object or string.")

    universal = payload.get("universal")
    specific = payload.get("specific", {})
    universal_normalized = normalize_universal(
        universal, json.dumps(payload, ensure_ascii=False), strict
    )

    return {"universal": universal_normalized, "specific": specific}


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


def run_welder(input_path: str, output_path: str, strict: bool) -> Dict[str, Any]:
    source_path = Path(input_path)
    raw_text = source_path.read_text(encoding="utf-8").strip()

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        payload = raw_text

    normalized = normalize_payload(payload, strict=strict)
    write_json(Path(output_path), normalized)
    print(json.dumps(normalized, ensure_ascii=False, indent=2))
    return normalized


def main() -> None:
    args = parse_args()
    run_welder(args.input, args.output, args.strict)


if __name__ == "__main__":
    main()
