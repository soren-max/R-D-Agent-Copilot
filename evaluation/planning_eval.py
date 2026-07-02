"""Run Router/Planner against planning eval cases and write a report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.agent.planner import Planner
from app.agent.router import IntentRouter
from app.core.config import LLMSettings
from evaluation.plan_quality import PlanQualityResult, evaluate_plan_quality

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES_PATH = ROOT / "data" / "eval" / "planning_cases.jsonl"
DEFAULT_REPORT_PATH = ROOT / "data" / "eval" / "planning_eval_report.md"
DEFAULT_BAD_CASES_PATH = ROOT / "data" / "eval" / "bad_cases.jsonl"


class OfflineProvider:
    settings = LLMSettings(enabled=False, provider="offline", model="rule_based")

    def is_available(self) -> bool:
        return False

    def generate(self, prompt_name: str, system_prompt: str, user_prompt: str):
        raise RuntimeError("offline planning evaluation does not call LLM")


def load_planning_cases(path: Path = DEFAULT_CASES_PATH) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            cases.append(json.loads(line))
    return cases


def run_planning_eval(
    cases_path: Path = DEFAULT_CASES_PATH,
    report_path: Path = DEFAULT_REPORT_PATH,
    bad_cases_path: Path = DEFAULT_BAD_CASES_PATH,
) -> dict[str, Any]:
    offline_provider = OfflineProvider()
    router = IntentRouter(llm_provider=offline_provider)
    planner = Planner(llm_provider=offline_provider)
    cases = load_planning_cases(cases_path)
    results: list[PlanQualityResult] = []
    for case in cases:
        route = router.route(case["question"])
        plan = planner.plan(case["question"], route)
        actual_tools = [step.tool for step in plan.steps]
        actual_steps = [step.step_name or step.action for step in plan.steps]
        results.append(evaluate_plan_quality(case, route.intent, actual_tools, actual_steps))

    metrics = summarize_results(results)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(metrics, results), encoding="utf-8")
    _write_bad_cases(results, bad_cases_path)
    return {
        **metrics,
        "results": [result.to_dict() for result in results],
        "report_path": str(report_path),
    }


def _write_bad_cases(results: list[PlanQualityResult], path: Path) -> None:
    failed = [result.to_dict() for result in results if result.failure_reasons]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in failed) + ("\n" if failed else ""),
        encoding="utf-8",
    )


def summarize_results(results: list[PlanQualityResult]) -> dict[str, Any]:
    total = max(1, len(results))
    return {
        "total_cases": len(results),
        "router_intent_accuracy": round(sum(r.intent_score for r in results) / total, 4),
        "required_tools_hit_rate": round(sum(r.required_tools_score for r in results) / total, 4),
        "step_order_accuracy": round(sum(r.step_order_score for r in results) / total, 4),
        "safety_tool_recall": round(sum(r.safety_score for r in results) / total, 4),
        "average_plan_quality_score": round(sum(r.plan_quality_score for r in results) / total, 4),
        "failed_cases": sum(1 for r in results if r.failure_reasons),
    }


def render_report(metrics: dict[str, Any], results: list[PlanQualityResult]) -> str:
    lines = [
        "# Planning Evaluation Report",
        "",
        f"- Total cases: {metrics['total_cases']}",
        f"- Router intent accuracy: {metrics['router_intent_accuracy']}",
        f"- Required tools hit rate: {metrics['required_tools_hit_rate']}",
        f"- Step order accuracy: {metrics['step_order_accuracy']}",
        f"- Safety tool recall: {metrics['safety_tool_recall']}",
        f"- Average plan quality score: {metrics['average_plan_quality_score']}",
        f"- Failed cases: {metrics['failed_cases']}",
        "",
        "| case_id | expected_intent | actual_intent | score | failure_reasons |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for result in results:
        reasons = ",".join(result.failure_reasons)
        lines.append(
            f"| {result.case_id} | {result.expected_intent} | {result.actual_intent} | "
            f"{result.plan_quality_score} | {reasons} |"
        )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    print(json.dumps(run_planning_eval(), ensure_ascii=False, indent=2))
