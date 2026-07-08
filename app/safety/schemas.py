"""Safety guard schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolInput(BaseModel):
    """Normalized tool input checked before deterministic execution."""

    tool_name: str = Field(default="")
    query: str
    action: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)


class SafetyDecision(BaseModel):
    """Stable safety decision returned by the guard."""

    blocked: bool = False
    reason: str = ""
    tool_name: str = ""
    input_summary: str = ""
    safety_status: str = "allowed"
    risk_level: str = "low"
    reasons: list[str] = Field(default_factory=list)
    matched_patterns: list[str] = Field(default_factory=list)
    blocked_tools: list[str] = Field(default_factory=list)

    @classmethod
    def allow(cls, *, tool_name: str = "", input_summary: str = "") -> "SafetyDecision":
        return cls(tool_name=tool_name, input_summary=input_summary)

    @classmethod
    def block(
        cls,
        *,
        reason: str,
        tool_name: str = "",
        input_summary: str = "",
        matched_patterns: list[str] | None = None,
    ) -> "SafetyDecision":
        return cls(
            blocked=True,
            reason=reason,
            tool_name=tool_name,
            input_summary=input_summary,
            safety_status="blocked",
            risk_level="high",
            reasons=[reason],
            matched_patterns=matched_patterns or [],
            blocked_tools=[tool_name] if tool_name else [],
        )
