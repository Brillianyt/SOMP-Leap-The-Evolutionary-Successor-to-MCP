#!/usr/bin/env python3
"""
SOMP schema helpers (MVP).

Provides normalization utilities for the universal layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping


@dataclass
class UniversalLayer:
    intent: str
    summary: str
    confidence: float


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def normalize_universal(
    universal: Any, fallback_text: str, strict: bool
) -> Dict[str, Any]:
    if not isinstance(universal, Mapping):
        if strict:
            raise ValueError("Missing universal layer.")
        summary = fallback_text.strip() or "无摘要"
        universal = {
            "intent": "unspecified",
            "summary": summary,
            "confidence": 0.5,
        }

    intent = str(universal.get("intent", "unspecified"))
    summary = str(universal.get("summary", "无摘要"))
    confidence = clamp(float(universal.get("confidence", 0.5)))

    if strict and (not intent or not summary):
        raise ValueError("Universal layer missing required fields.")

    return {
        "intent": intent,
        "summary": summary,
        "confidence": confidence,
    }
