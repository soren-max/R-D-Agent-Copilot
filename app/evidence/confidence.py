from __future__ import annotations

from statistics import mean
from typing import Any

from app.evidence.schemas import EvidenceItem, RootCauseCandidate


def clamp_confidence(value: Any, default: float = 0.6) -> float:
    if isinstance(value, bool):
        return default
    if not isinstance(value, (int, float)):
        return default
    return round(max(0.0, min(1.0, float(value))), 2)


def evidence_confidence(tool_result: dict[str, Any]) -> float:
    confidence = clamp_confidence(tool_result.get("confidence"), default=0.6)
    status = tool_result.get("status", "success")
    if status == "failed" or tool_result.get("error"):
        return min(confidence, 0.3)
    if status == "skipped":
        return min(confidence, 0.2)
    return confidence


def candidate_confidence(
    evidence_types: set[str],
    failed_tool_count: int = 0,
    evaluation_score: float | None = None,
) -> float:
    if {"log", "config"}.issubset(evidence_types):
        base = 0.88
    elif {"log", "git"}.issubset(evidence_types):
        base = 0.8
    elif len(evidence_types.intersection({"log", "config", "git", "rag"})) >= 2:
        base = 0.76
    elif evidence_types.intersection({"log", "config", "git", "rag"}):
        base = 0.66
    else:
        base = 0.5

    if evaluation_score is not None:
        base = (base * 0.85) + (evaluation_score * 0.15)
    base -= min(failed_tool_count * 0.08, 0.24)
    return clamp_confidence(base)


def overall_confidence(
    candidates: list[RootCauseCandidate],
    evidence_items: list[EvidenceItem],
    tool_success_rate: float,
    evaluation_score: float | None = None,
) -> float:
    if candidates:
        base = mean(candidate.confidence for candidate in candidates)
    elif evidence_items:
        base = mean(item.confidence for item in evidence_items)
    else:
        base = 0.0

    score = (base * 0.7) + (tool_success_rate * 0.2)
    if evaluation_score is not None:
        score += evaluation_score * 0.1
    else:
        score += base * 0.1
    return clamp_confidence(score, default=0.0)
