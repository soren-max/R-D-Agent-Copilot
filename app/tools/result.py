"""Standard tool gateway result model."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ToolGatewayStatus = Literal["success", "error", "partial_success", "blocked"]


class StandardToolResult(BaseModel):
    """Normalized result emitted by ToolGateway."""

    tool_name: str
    status: ToolGatewayStatus
    latency_ms: int = 0
    input_hash: str = ""
    evidence_count: int = 0
    safe_summary: str = ""
    error_code: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    def legacy_status(self) -> str:
        if self.status in {"error", "blocked"}:
            return "failed"
        return self.status
