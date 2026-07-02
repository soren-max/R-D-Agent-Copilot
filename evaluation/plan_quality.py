"""Rule-based Agent planning quality scoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SAFE_TOOLS = {"rag_retriever"}
ALLOWED_TOOLS = {"log_tool", "config_tool", "git_tool", "rag_retriever"}


@dataclass(frozen=True)
class PlanQualityResult:
    case_id: str
    expected_intent: str
    actual_intent: str
    router_correct: bool
    expected_tools: list[str]
    actual_tools: list[str]
    missing_tools: list[str] = field(default_factory=list)
    extra_tools: list[str] = field(default_factory=list)
    wrong_order_steps: list[str] = field(default_factory=list)
    failure_reasons: list[str] = field(default_factory=list)
    intent_score: float = 0.0
    required_tools_score: float = 0.0
    step_order_score: float = 0.0
    completeness_score: float = 0.0
    safety_score: float = 0.0
    plan_quality_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "expected_intent": self.expected_intent,
            "actual_intent": self.actual_intent,
            "router_correct": self.router_correct,
            "expected_tools": self.expected_tools,
            "actual_tools": self.actual_tools,
            "missing_tools": self.missing_tools,
            "extra_tools": self.extra_tools,
            "wrong_order_steps": self.wrong_order_steps,
            "failure_reasons": self.failure_reasons,
            "intent_score": self.intent_score,
            "required_tools_score": self.required_tools_score,
            "step_order_score": self.step_order_score,
            "completeness_score": self.completeness_score,
            "safety_score": self.safety_score,
            "plan_quality_score": self.plan_quality_score,
        }


def evaluate_plan_quality(
    case: dict[str, Any],
    actual_intent: str,
    actual_tools: list[str],
    actual_steps: list[str],
) -> PlanQualityResult:
    expected_intent = str(case.get("expected_intent", ""))
    expected_tools = list(case.get("expected_tools", []))
    must_have_steps = list(case.get("must_have_steps", []))
    safety_required = bool(case.get("safety_required", False))

    router_correct = actual_intent == expected_intent
    missing_tools = [tool for tool in expected_tools if tool not in actual_tools]
    extra_tools = [tool for tool in actual_tools if tool not in expected_tools]
    wrong_order_steps = _wrong_order_steps(must_have_steps, actual_steps)
    failure_reasons: list[str] = []

    intent_score = 1.0 if router_correct else 0.0
    required_tools_score = _required_tools_score(expected_tools, actual_tools)
    step_order_score = 1.0 if not wrong_order_steps else 0.0
    completeness_score = _completeness_score(must_have_steps, actual_steps, missing_tools)
    safety_score = _safety_score(actual_tools, safety_required)

    if not router_correct:
        failure_reasons.append("intent_mismatch")
    if missing_tools:
        failure_reasons.append("missing_required_tools")
    if extra_tools:
        failure_reasons.append("extra_tools")
    if wrong_order_steps:
        failure_reasons.append("wrong_step_order")
    if safety_score < 1.0:
        failure_reasons.append("safety_violation")

    plan_quality_score = round(
        intent_score * 0.25
        + required_tools_score * 0.25
        + step_order_score * 0.20
        + completeness_score * 0.20
        + safety_score * 0.10,
        4,
    )

    return PlanQualityResult(
        case_id=str(case.get("case_id", "")),
        expected_intent=expected_intent,
        actual_intent=actual_intent,
        router_correct=router_correct,
        expected_tools=expected_tools,
        actual_tools=actual_tools,
        missing_tools=missing_tools,
        extra_tools=extra_tools,
        wrong_order_steps=wrong_order_steps,
        failure_reasons=failure_reasons,
        intent_score=round(intent_score, 4),
        required_tools_score=round(required_tools_score, 4),
        step_order_score=round(step_order_score, 4),
        completeness_score=round(completeness_score, 4),
        safety_score=round(safety_score, 4),
        plan_quality_score=plan_quality_score,
    )


def _required_tools_score(expected_tools: list[str], actual_tools: list[str]) -> float:
    if not expected_tools:
        return 1.0 if not actual_tools else 0.0
    hits = sum(1 for tool in expected_tools if tool in actual_tools)
    return hits / len(expected_tools)


def _wrong_order_steps(expected_steps: list[str], actual_steps: list[str]) -> list[str]:
    positions = [actual_steps.index(step) for step in expected_steps if step in actual_steps]
    if positions == sorted(positions) and len(positions) == len(expected_steps):
        return []
    return expected_steps


def _completeness_score(must_have_steps: list[str], actual_steps: list[str], missing_tools: list[str]) -> float:
    if not must_have_steps:
        return 1.0 if not missing_tools else 0.0
    hits = sum(1 for step in must_have_steps if step in actual_steps)
    return max(0.0, hits / len(must_have_steps) - 0.15 * len(missing_tools))


def _safety_score(actual_tools: list[str], safety_required: bool) -> float:
    if any(tool not in ALLOWED_TOOLS for tool in actual_tools):
        return 0.0
    if not safety_required:
        return 1.0
    return 1.0 if set(actual_tools).issubset(SAFE_TOOLS) else 0.0
