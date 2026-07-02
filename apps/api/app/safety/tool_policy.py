"""Tool allowlist and denylist policy."""

from __future__ import annotations

from app.core.models import Plan
from apps.api.app.safety.schemas import SafetyCheckResult, ToolPolicyResult

ALLOWED_TOOLS = {"log_tool", "config_tool", "git_tool", "rag_retriever"}
DENIED_TOOLS = {"shell_tool", "db_write_tool", "external_api_tool", "secret_tool"}
SAFE_ONLY_TOOLS = {"rag_retriever"}


def validate_plan_tools(plan: Plan, safety: SafetyCheckResult | None = None) -> ToolPolicyResult:
    safety = safety or SafetyCheckResult()
    tools = [step.tool for step in plan.steps]
    blocked_tools: list[str] = []
    reasons: list[str] = []

    for tool in tools:
        if tool in DENIED_TOOLS or tool not in ALLOWED_TOOLS:
            blocked_tools.append(tool)
            reasons.append("tool_not_allowed")

    if safety.risk_level in {"medium", "high"}:
        unsafe_tools = [tool for tool in tools if tool not in SAFE_ONLY_TOOLS]
        if unsafe_tools:
            blocked_tools.extend(unsafe_tools)
            reasons.append("safety_risk_requires_safe_tools_only")

    blocked_tools = list(dict.fromkeys(blocked_tools))
    return ToolPolicyResult(
        allowed=not blocked_tools,
        allowed_tools=sorted(ALLOWED_TOOLS),
        denied_tools=sorted(DENIED_TOOLS),
        blocked_tools=blocked_tools,
        reasons=list(dict.fromkeys(reasons)),
    )
