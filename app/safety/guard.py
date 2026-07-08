"""Deterministic safety guard for prompt and tool-call boundaries."""

from __future__ import annotations

from typing import Any

from app.safety.policies import DANGEROUS_ACTION_PATTERNS, PROMPT_INJECTION_PATTERNS, TOOL_ALLOWLIST
from app.safety.schemas import SafetyDecision, ToolInput


def _summarize(value: Any, max_length: int = 120) -> str:
    text = str(value).replace("\n", " ").strip()
    if len(text) <= max_length:
        return text
    return f"{text[: max_length - 3]}..."


class SafetyGuard:
    """Rule-based guard that never calls LLMs or external APIs."""

    allowlist = TOOL_ALLOWLIST

    def check_prompt(self, query: Any) -> SafetyDecision:
        if not isinstance(query, str):
            return SafetyDecision.block(reason="invalid_query", input_summary=_summarize(query))

        lowered = query.lower()
        matched = [pattern for pattern in PROMPT_INJECTION_PATTERNS if pattern.lower() in lowered]
        if matched:
            return SafetyDecision.block(
                reason="prompt_injection_risk",
                input_summary=_summarize(query),
                matched_patterns=matched,
            )

        return SafetyDecision.allow(input_summary=_summarize(query))

    def validate_tool_input(self, tool_name: Any, payload: dict[str, Any] | None = None) -> SafetyDecision:
        payload = payload or {}
        if not isinstance(tool_name, str) or not tool_name.strip():
            return SafetyDecision.block(reason="empty_tool_name", input_summary=_summarize(payload))

        normalized_tool_name = tool_name.strip()
        if normalized_tool_name not in self.allowlist:
            return SafetyDecision.block(
                reason="unknown_tool",
                tool_name=normalized_tool_name,
                input_summary=_summarize(payload),
            )

        query = payload.get("query")
        if not isinstance(query, str):
            return SafetyDecision.block(
                reason="invalid_query",
                tool_name=normalized_tool_name,
                input_summary=_summarize(payload),
            )

        action = str(payload.get("action", "")).lower()
        if any(pattern.lower() in action for pattern in DANGEROUS_ACTION_PATTERNS):
            return SafetyDecision.block(
                reason="dangerous_action",
                tool_name=normalized_tool_name,
                input_summary=_summarize(payload),
                matched_patterns=[action],
            )

        prompt_decision = self.check_prompt(query)
        if prompt_decision.blocked:
            return SafetyDecision.block(
                reason=prompt_decision.reason,
                tool_name=normalized_tool_name,
                input_summary=prompt_decision.input_summary,
                matched_patterns=prompt_decision.matched_patterns,
            )

        ToolInput(tool_name=normalized_tool_name, query=query, action=str(payload.get("action", "")))
        return SafetyDecision.allow(tool_name=normalized_tool_name, input_summary=_summarize(query))


def check_prompt_injection(query: Any) -> SafetyDecision:
    return SafetyGuard().check_prompt(query)


def validate_tool_input(tool_name: Any, payload: dict[str, Any] | None = None) -> SafetyDecision:
    return SafetyGuard().validate_tool_input(tool_name, payload)
