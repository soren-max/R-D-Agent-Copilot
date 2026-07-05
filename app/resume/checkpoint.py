"""Run checkpoint model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunCheckpoint(BaseModel):
    """Recoverable state for one Agent run."""

    run_id: str
    query: str
    route: dict[str, Any] = Field(default_factory=dict)
    plan: dict[str, Any] = Field(default_factory=dict)
    completed_steps: list[int] = Field(default_factory=list)
    pending_steps: list[int] = Field(default_factory=list)
    tool_evidence_summary: str = ""
    rag_evidence_summary: str = ""
    context_metadata: dict[str, Any] = Field(default_factory=dict)
    last_error: str = ""
    status: str = "running"
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
