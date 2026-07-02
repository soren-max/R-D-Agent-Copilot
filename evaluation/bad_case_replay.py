"""Save and replay failed planning evaluation cases."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evaluation.plan_quality import evaluate_plan_quality
from evaluation.planning_eval import DEFAULT_BAD_CASES_PATH, DEFAULT_CASES_PATH, ROOT, OfflineProvider, load_planning_cases, render_report, summarize_results
from app.agent.planner import Planner
from app.agent.router import IntentRouter

DEFAULT_REPLAY_REPORT_PATH = ROOT / "data" / "eval" / "bad_case_replay_report.md"


def save_bad_cases(eval_results: list[dict[str, Any]], path: Path = DEFAULT_BAD_CASES_PATH) -> int:
    failed = [result for result in eval_results if result.get("failure_reasons")]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in failed) + ("\n" if failed else ""),
        encoding="utf-8",
    )
    return len(failed)


def load_bad_cases(path: Path = DEFAULT_BAD_CASES_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def replay_bad_cases(
    bad_cases_path: Path = DEFAULT_BAD_CASES_PATH,
    all_cases_path: Path = DEFAULT_CASES_PATH,
    report_path: Path = DEFAULT_REPLAY_REPORT_PATH,
) -> dict[str, Any]:
    bad_cases = load_bad_cases(bad_cases_path)
    all_cases = {case["case_id"]: case for case in load_planning_cases(all_cases_path)}
    offline_provider = OfflineProvider()
    router = IntentRouter(llm_provider=offline_provider)
    planner = Planner(llm_provider=offline_provider)
    replay_results = []
    quality_results = []
    for bad_case in bad_cases:
        case = all_cases.get(bad_case["case_id"], bad_case)
        route = router.route(case["question"])
        plan = planner.plan(case["question"], route)
        quality = evaluate_plan_quality(
            case,
            route.intent,
            [step.tool for step in plan.steps],
            [step.step_name or step.action for step in plan.steps],
        )
        status = "fixed" if not quality.failure_reasons else "still_failed"
        replay_results.append({**quality.to_dict(), "replay_status": status})
        quality_results.append(quality)

    metrics = summarize_results(quality_results)
    report = render_report(metrics, quality_results)
    report += "\n## Replay Status\n\n"
    for result in replay_results:
        report += f"- {result['case_id']}: {result['replay_status']}\n"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return {
        "total_replayed": len(replay_results),
        "fixed": sum(1 for result in replay_results if result["replay_status"] == "fixed"),
        "still_failed": sum(1 for result in replay_results if result["replay_status"] == "still_failed"),
        "results": replay_results,
        "report_path": str(report_path),
    }


if __name__ == "__main__":
    print(json.dumps(replay_bad_cases(), ensure_ascii=False, indent=2))
