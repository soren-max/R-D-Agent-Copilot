import json

from app.eval import EvaluationReportV2, EvaluationV2Evaluator
from app.eval.artifact_aggregator import EvaluationArtifactAggregator


def _payload():
    return {
        "run_id": "run-v2",
        "query": "为什么订单接口报500？",
        "answer": "【初步判断】基于日志和知识库证据判断配置差异。\n【排查步骤】建议同步配置。",
        "tool_results": [
            {"tool": "log_tool", "tool_name": "log_tool", "status": "success", "latency_ms": 10, "result": "ERROR 500"},
            {"tool": "config_tool", "tool_name": "config_tool", "status": "failed", "latency_ms": 20, "error": "file_not_found"},
            {
                "tool": "rag_retriever",
                "tool_name": "rag_retriever",
                "status": "success",
                "latency_ms": 30,
                "documents": [
                    {"source": "service-logs.md", "title": "日志", "score": 0.9, "content": "500"},
                    {"content": "missing source"},
                ],
                "rag_metadata": {"grounding_status": "grounded"},
            },
        ],
        "trace": {
            "trace_id": "run-v2",
            "steps": [
                {
                    "stage": "executor",
                    "tool_calls": [
                        {"tool_name": "log_tool", "tool_status": "success", "latency_ms": 10},
                        {"tool_name": "config_tool", "tool_status": "error", "latency_ms": 20, "error_code": "file_not_found"},
                        {"tool_name": "git_tool", "tool_status": "blocked", "latency_ms": 1, "error_code": "duplicate_call"},
                        {"tool_name": "rag_retriever", "tool_status": "partial_success", "latency_ms": 30},
                    ],
                },
                {
                    "stage": "synthesizer",
                    "llm_used": False,
                    "llm_error": "llm_disabled",
                    "model": "deepseek-v4-flash",
                    "llm_usage": {"provider": "deepseek", "model": "deepseek-v4-flash", "latency_ms": 0},
                    "context_metadata": {
                        "total_chars_before": 1000,
                        "total_chars_after": 500,
                        "compression_ratio": 0.5,
                        "section_char_counts": {"current_query": len("为什么订单接口报500？")},
                        "reduced_sections": ["tool_evidence"],
                        "memory_hit_count": 2,
                        "fresh_memory_count": 1,
                        "stale_memory_count": 1,
                    },
                    "checkpoint_created": True,
                },
            ],
        },
        "evidence_chain": {
            "evidence_items": [{"id": "ev_log_001"}, {"id": "ev_rag_001"}],
            "root_cause_candidates": [{"title": "配置差异", "supporting_evidence_ids": ["ev_log_001"]}],
        },
        "checkpoint": {"completed_steps": [1, 1, 2]},
        "resume_result": {"status": "completed", "resumed_completed_steps_count": 2, "resumed_pending_steps_count": 0},
    }


def test_can_create_evaluation_report_v2():
    report = EvaluationReportV2(run_id="run-1", overall=0.8)

    assert report.run_id == "run-1"
    assert report.context.compression_ratio == 1.0


def test_context_metrics_from_context_metadata():
    report = EvaluationV2Evaluator().evaluate(_payload())

    assert report.context.prompt_chars_before == 1000
    assert report.context.prompt_chars_after == 500
    assert report.context.compression_ratio == 0.5
    assert report.context.current_query_preserved is True
    assert report.context.reduced_sections == ["tool_evidence"]


def test_tool_metrics_count_statuses():
    report = EvaluationV2Evaluator().evaluate(_payload())

    assert report.tool.tool_success_rate == 0.25
    assert report.tool.tool_error_count == 1
    assert report.tool.tool_blocked_count == 1
    assert report.tool.partial_success_count == 1
    assert report.tool.tool_status_counts["blocked"] == 1


def test_rag_missing_source_increases_missing_source_count():
    report = EvaluationV2Evaluator().evaluate(_payload())

    assert report.rag.rag_hit_count == 2
    assert report.rag.missing_source_count == 1
    assert report.rag.source_coverage == 0.5


def test_stale_memory_is_counted():
    report = EvaluationV2Evaluator().evaluate(_payload())

    assert report.memory.memory_hit_count == 2
    assert report.memory.fresh_memory_count == 1
    assert report.memory.stale_memory_count == 1


def test_memory_misused_as_current_fact_is_flagged_without_current_evidence():
    payload = _payload()
    payload["answer"] = "本次根因是历史配置差异。"
    payload["tool_results"] = []

    report = EvaluationV2Evaluator().evaluate(payload)

    assert report.memory.memory_misused_as_current_fact_count == 1


def test_resume_duplicated_step_count_is_counted():
    report = EvaluationV2Evaluator().evaluate(_payload())

    assert report.resume.checkpoint_created is True
    assert report.resume.resume_success is True
    assert report.resume.duplicated_step_count == 1


def test_evidence_chain_complete_is_judged():
    report = EvaluationV2Evaluator().evaluate(_payload())

    assert report.evidence.evidence_chain_complete is True
    assert report.evidence.evidence_refs_count == 1
    assert report.evidence.root_cause_supported is True
    assert report.evidence.fix_steps_supported is True


def test_fallback_provider_metrics_with_llm_disabled():
    report = EvaluationV2Evaluator().evaluate(_payload())

    assert report.provider.llm_enabled is False
    assert report.provider.fallback_used is True
    assert report.provider.provider_error_count == 1


def test_artifact_aggregator_saves_report_and_summary(tmp_path):
    aggregator = EvaluationArtifactAggregator(tmp_path)
    report = aggregator.aggregate_run(_payload(), save=True)
    summary = aggregator.write_summary([report])

    artifact = tmp_path / "evaluation-v2-run-v2.json"
    assert artifact.exists()
    assert json.loads(artifact.read_text(encoding="utf-8"))["run_id"] == "run-v2"
    assert (tmp_path / "evaluation-v2-summary.json").exists()
    assert summary["run_count"] == 1
