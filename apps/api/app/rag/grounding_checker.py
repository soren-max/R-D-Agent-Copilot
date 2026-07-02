"""Claim-level grounding checker."""

from __future__ import annotations

from apps.api.app.rag.chunker import extract_keywords
from apps.api.app.rag.claim_extractor import ClaimExtractor
from apps.api.app.rag.schemas import GroundedClaim, GroundingCheckResult, UnsupportedClaim


class GroundingChecker:
    """Check whether answer claims are supported by evidence excerpts."""

    def __init__(self, extractor: ClaimExtractor | None = None, min_overlap: int = 1) -> None:
        self.extractor = extractor or ClaimExtractor()
        self.min_overlap = min_overlap

    def check(self, answer: str, evidence: list[dict[str, object]]) -> GroundingCheckResult:
        claims = self.extractor.extract(answer)
        if not claims:
            return GroundingCheckResult(grounding_score=1.0, evidence_count=len(evidence))

        evidence_terms = [
            (
                str(item.get("chunk_id", "")),
                set(extract_keywords(str(item.get("content_excerpt", "")))),
            )
            for item in evidence
        ]
        grounded: list[GroundedClaim] = []
        unsupported: list[UnsupportedClaim] = []
        for claim in claims:
            claim_terms = set(extract_keywords(claim.text))
            supporting_ids: list[str] = []
            best_overlap = 0
            for evidence_id, terms in evidence_terms:
                overlap = len(claim_terms.intersection(terms))
                if overlap >= self.min_overlap:
                    supporting_ids.append(evidence_id)
                    best_overlap = max(best_overlap, overlap)
            if supporting_ids:
                grounded.append(
                    GroundedClaim(
                        claim_id=claim.claim_id,
                        text=claim.text,
                        supporting_evidence_ids=supporting_ids,
                        score=min(1.0, best_overlap / max(1, len(claim_terms))),
                    )
                )
            else:
                unsupported.append(
                    UnsupportedClaim(
                        claim_id=claim.claim_id,
                        text=claim.text,
                        reason="no_supporting_evidence_overlap",
                    )
                )

        score = len(grounded) / max(1, len(claims))
        return GroundingCheckResult(
            grounding_score=round(score, 4),
            grounded_claims=grounded,
            unsupported_claims=unsupported,
            evidence_count=len(evidence),
        )
