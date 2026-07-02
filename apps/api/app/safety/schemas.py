"""Safety data contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SafetyCheckResult(BaseModel):
    safety_status: str = Field(default="allowed", description="allowed | blocked")
    risk_level: str = Field(default="low", description="low | medium | high")
    reasons: list[str] = Field(default_factory=list)
    matched_patterns: list[str] = Field(default_factory=list)

    @property
    def blocked(self) -> bool:
        return self.safety_status == "blocked"


class ToolPolicyResult(BaseModel):
    allowed: bool = True
    allowed_tools: list[str] = Field(default_factory=list)
    denied_tools: list[str] = Field(default_factory=list)
    blocked_tools: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class KbFilterResult(BaseModel):
    source: str
    allowed: bool = True
    reason: str = ""
