from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    id: str
    type: str = Field(description="Evidence type: log | config | git | rag | evaluation")
    source: str = ""
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)
    related_tool: str = ""


class RootCauseCandidate(BaseModel):
    title: str
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    reason: str


class EvidenceChain(BaseModel):
    overall_confidence: float = Field(ge=0.0, le=1.0)
    root_cause_candidates: list[RootCauseCandidate] = Field(default_factory=list)
    evidence_items: list[EvidenceItem] = Field(default_factory=list)
