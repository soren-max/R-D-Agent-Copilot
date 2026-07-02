"""Shared v0.4.0 RAG trust schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RerankResult(BaseModel):
    chunk_id: str
    source: str
    original_score: float = 0.0
    rerank_score: float = 0.0
    final_score: float = 0.0
    reason: str = ""


class ExtractedClaim(BaseModel):
    claim_id: str
    text: str
    section: str = ""


class GroundedClaim(BaseModel):
    claim_id: str
    text: str
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    score: float = 0.0


class UnsupportedClaim(BaseModel):
    claim_id: str
    text: str
    reason: str


class GroundingCheckResult(BaseModel):
    grounding_score: float = Field(ge=0.0, le=1.0)
    grounded_claims: list[GroundedClaim] = Field(default_factory=list)
    unsupported_claims: list[UnsupportedClaim] = Field(default_factory=list)
    evidence_count: int = 0
