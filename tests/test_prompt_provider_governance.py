import json

import app.agent.synthesizer as synthesizer_module
from app.agent.synthesizer import AnswerSynthesizer
from app.api.chat import chat_endpoint
from app.core.models import ChatRequest, Plan, PlanStep, RouterResult
from apps.api.app.context.metadata import ContextMetadata
from apps.api.app.context.sections import ContextPackage, ContextSection
from app.eval import EvaluationV2Evaluator


def _clear_llm_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-v4-flash")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")


def _synthesizer_step(data):
    return [step for step in data["trace"]["steps"] if step["stage"] == "synthesizer"][0]


def test_llm_disabled_final_report_schema_valid(monkeypatch):
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("LLM_ENABLED", "false")

    data = chat_endpoint(ChatRequest(query="为什么订单接口报500？")).model_dump()
    step = _synthesizer_step(data)

    assert data["answer_source"] == "fallback"
    assert step["provider_metadata"]["fallback_used"] is True
    assert step["provider_metadata"]["schema_valid"] is True
    assert step["schema_valid"] is True
    assert set(step["parsed_output"]) >= {"summary", "root_cause", "evidence", "fix_steps", "confidence", "risks"}


def test_provider_error_uses_fallback_and_records_metadata(monkeypatch):
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-api-key")

    def fail_generate(self, system_prompt, user_prompt):
        raise RuntimeError("network failed")

    monkeypatch.setattr(synthesizer_module.LLMClient, "generate", fail_generate)

    data = chat_endpoint(ChatRequest(query="为什么订单接口报500？")).model_dump()
    step = _synthesizer_step(data)

    assert data["answer_source"] == "fallback"
    assert step["provider_metadata"]["fallback_used"] is True
    assert step["provider_metadata"]["provider_error_code"] == "RuntimeError"
    assert step["provider_metadata"]["schema_valid"] is True
    assert set(step["parsed_output"]) >= {"summary", "root_cause", "evidence", "fix_steps", "confidence", "risks"}


def test_invalid_json_output_is_marked_schema_invalid(monkeypatch):
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-api-key")

    def invalid_generate(self, system_prompt, user_prompt):
        return "1. 初步判断\n模拟中文回答"

    monkeypatch.setattr(synthesizer_module.LLMClient, "generate", invalid_generate)

    data = chat_endpoint(ChatRequest(query="为什么订单接口报500？")).model_dump()
    step = _synthesizer_step(data)

    assert data["answer_source"] == "llm"
    assert step["provider_metadata"]["schema_valid"] is False
    assert step["provider_metadata"]["provider_error_code"] == "invalid_json"
    assert set(step["parsed_output"]) >= {"summary", "root_cause", "evidence", "fix_steps", "confidence", "risks"}


def test_prompt_version_is_written_to_trace(monkeypatch):
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("LLM_ENABLED", "false")

    data = chat_endpoint(ChatRequest(query="什么是配置中心？")).model_dump()
    step = _synthesizer_step(data)

    assert step["prompt_version"] == "answer_synthesizer_v1"
    assert step["provider_metadata"]["prompt_version"] == "answer_synthesizer_v1"


def test_provider_metadata_is_aggregated_by_evaluation_v2():
    payload = {
        "run_id": "run-provider",
        "query": "为什么订单接口报500？",
        "answer": "当前使用 fallback。",
        "tool_results": [],
        "trace": {
            "trace_id": "run-provider",
            "steps": [
                {
                    "stage": "synthesizer",
                    "provider_metadata": {
                        "prompt_version": "answer_synthesizer_v1",
                        "model_provider": "deepseek",
                        "model_name": "deepseek-v4-flash",
                        "llm_enabled": True,
                        "fallback_used": True,
                        "schema_valid": False,
                        "generation_latency_ms": 12,
                        "provider_error_code": "invalid_json",
                        "provider_error_message": "invalid_json",
                    },
                }
            ],
        },
    }

    report = EvaluationV2Evaluator().evaluate(payload)

    assert report.provider.prompt_version == "answer_synthesizer_v1"
    assert report.provider.provider_name == "deepseek"
    assert report.provider.fallback_used is True
    assert report.provider.schema_valid is False
    assert report.provider.provider_error_count == 1


def test_incident_memory_is_not_used_as_current_evidence(monkeypatch):
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("LLM_ENABLED", "false")
    memory_payload = [{
        "memory_id": "mem-1",
        "service": "order-service",
        "symptom": "接口 500",
        "root_cause": "历史配置差异",
        "fix": "回滚配置",
        "freshness_status": "fresh",
    }]
    context_package = ContextPackage(
        sections=[
            ContextSection(name="incident_memory", content=json.dumps(memory_payload, ensure_ascii=False)),
        ],
        metadata=ContextMetadata(memory_hit_count=1, fresh_memory_count=1),
    )
    route = RouterResult(type="complex_troubleshooting", intent="log_analysis", confidence=0.9, reason="test")
    plan = Plan(
        plan_type="troubleshooting_plan",
        steps=[PlanStep(id=1, action="query_logs", tool="log_tool", description="query logs")],
    )

    result = AnswerSynthesizer().synthesize(
        "为什么订单接口报500？",
        route,
        plan,
        [],
        use_llm=False,
        context_package=context_package,
    )

    assert "不是当前证据" in result["answer"]
    assert result["parsed_output"]["root_cause"] != "历史配置差异"
    assert any("Incident Memory" in risk for risk in result["parsed_output"]["risks"])
