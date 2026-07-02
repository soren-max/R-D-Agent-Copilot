"""Grounding rules for evidence-based answers."""

from __future__ import annotations

from dataclasses import dataclass

from apps.api.app.rag.evidence import Evidence


@dataclass(frozen=True)
class GroundingResult:
    grounding_status: str
    no_evidence_reason: str = ""


def evaluate_grounding(evidence: list[Evidence]) -> GroundingResult:
    if not evidence:
        return GroundingResult(
            grounding_status="insufficient_evidence",
            no_evidence_reason="no_retrieved_chunks",
        )
    return GroundingResult(grounding_status="grounded")
