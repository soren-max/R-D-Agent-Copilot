import json
from pathlib import Path

from scripts.eval_planning import evaluate as evaluate_planning
from scripts.eval_rag import evaluate as evaluate_rag


def test_eval_scripts_write_stable_bad_case_replay():
    rag_metrics = evaluate_rag()
    planning_metrics = evaluate_planning()

    assert rag_metrics["total_cases"] >= 15
    assert planning_metrics["total_cases"] >= 12
    assert 0 <= planning_metrics["route_accuracy"] <= 1
    assert 0 <= planning_metrics["tool_selection_accuracy"] <= 1
    assert 0 <= planning_metrics["step_coverage"] <= 1
    assert isinstance(planning_metrics["missing_tool_cases"], list)
    assert isinstance(planning_metrics["bad_cases"], list)

    bad_cases_path = Path("data/reports/bad_cases.json")
    assert bad_cases_path.exists()
    replay = json.loads(bad_cases_path.read_text(encoding="utf-8"))
    assert set(replay) == {"rag_failed_cases", "planning_failed_cases"}
    assert isinstance(replay["rag_failed_cases"], list)
    assert isinstance(replay["planning_failed_cases"], list)
    assert Path("data/reports/planning_eval_result.json").exists()
    assert Path("data/reports/planning_eval_report.md").exists()
