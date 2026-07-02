import json
from pathlib import Path

from app.core.models import TraceStep
from evaluation.bad_case_replay import replay_bad_cases, save_bad_cases
from evaluation.plan_quality import evaluate_plan_quality
from evaluation.planning_eval import run_planning_eval


def _case(**overrides):
    data = {
        "case_id": "case_test",
        "question": "订单接口报500",
        "expected_intent": "log_analysis",
        "expected_tools": ["log_tool", "config_tool", "git_tool", "rag_retriever"],
        "must_have_steps": ["query_logs", "check_config", "analyze_git_diff", "retrieve_knowledge"],
        "safety_required": False,
    }
    data.update(overrides)
    return data


def test_router_intent_accuracy_calculation(tmp_path):
    report_path = tmp_path / "planning_eval_report.md"
    metrics = run_planning_eval(report_path=report_path)

    assert metrics["total_cases"] >= 30
    assert metrics["router_intent_accuracy"] == 1.0
    assert report_path.exists()


def test_required_tools_hit_rate_detects_missing_tools():
    result = evaluate_plan_quality(
        _case(),
        actual_intent="log_analysis",
        actual_tools=["log_tool", "rag_retriever"],
        actual_steps=["query_logs", "retrieve_knowledge"],
    )

    assert result.required_tools_score == 0.5
    assert result.missing_tools == ["config_tool", "git_tool"]
    assert "missing_required_tools" in result.failure_reasons


def test_step_order_score_detects_wrong_order():
    result = evaluate_plan_quality(
        _case(expected_tools=["log_tool", "config_tool", "rag_retriever"]),
        actual_intent="log_analysis",
        actual_tools=["log_tool", "config_tool", "rag_retriever"],
        actual_steps=["check_config", "query_logs", "retrieve_knowledge"],
    )

    assert result.step_order_score == 0.0
    assert result.wrong_order_steps
    assert "wrong_step_order" in result.failure_reasons


def test_safety_tool_recall_blocks_operational_tools():
    result = evaluate_plan_quality(
        _case(
            expected_intent="safety_risk",
            expected_tools=["rag_retriever"],
            must_have_steps=["retrieve_knowledge"],
            safety_required=True,
        ),
        actual_intent="safety_risk",
        actual_tools=["log_tool", "rag_retriever"],
        actual_steps=["query_logs", "retrieve_knowledge"],
    )

    assert result.safety_score == 0.0
    assert "safety_violation" in result.failure_reasons


def test_bad_case_save_writes_failed_cases(tmp_path):
    path = tmp_path / "bad_cases.jsonl"
    count = save_bad_cases(
        [
            {"case_id": "ok", "failure_reasons": []},
            {"case_id": "bad", "question": "x", "failure_reasons": ["intent_mismatch"]},
        ],
        path=path,
    )

    assert count == 1
    saved = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert saved[0]["case_id"] == "bad"


def test_bad_case_replay_marks_fixed_and_still_failed(tmp_path):
    all_cases = tmp_path / "planning_cases.jsonl"
    bad_cases = tmp_path / "bad_cases.jsonl"
    report = tmp_path / "bad_case_replay_report.md"

    fixed_case = _case(case_id="fixed", question="订单接口报500，帮我分析原因")
    still_failed_case = _case(
        case_id="still_failed",
        question="什么是配置中心？",
        expected_intent="log_analysis",
        expected_tools=["log_tool"],
        must_have_steps=["query_logs"],
    )
    all_cases.write_text(
        "\n".join(json.dumps(case, ensure_ascii=False) for case in [fixed_case, still_failed_case]),
        encoding="utf-8",
    )
    bad_cases.write_text(
        "\n".join(json.dumps({"case_id": case["case_id"]}, ensure_ascii=False) for case in [fixed_case, still_failed_case]),
        encoding="utf-8",
    )

    result = replay_bad_cases(bad_cases_path=bad_cases, all_cases_path=all_cases, report_path=report)

    statuses = {item["case_id"]: item["replay_status"] for item in result["results"]}
    assert statuses["fixed"] == "fixed"
    assert statuses["still_failed"] == "still_failed"
    assert report.exists()


def test_trace_step_contains_planning_eval_fields():
    step = TraceStep(
        stage="planning_eval",
        output="score=0.5",
        expected_intent="log_analysis",
        actual_intent="knowledge_qa",
        router_correct=False,
        expected_tools=["log_tool"],
        actual_tools=["rag_retriever"],
        missing_tools=["log_tool"],
        extra_tools=["rag_retriever"],
        plan_quality_score=0.5,
        failure_reasons=["intent_mismatch"],
    )

    data = step.model_dump()
    assert data["expected_intent"] == "log_analysis"
    assert data["missing_tools"] == ["log_tool"]
    assert data["plan_quality_score"] == 0.5
