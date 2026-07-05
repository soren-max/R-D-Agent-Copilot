from datetime import datetime, timedelta, timezone

from app.agent.synthesizer import AnswerSynthesizer
from app.api.chat import chat_endpoint
from app.core.models import ChatRequest, Plan, RouterResult
from app.memory import IncidentMemory, MemoryStore, evaluate_freshness
from apps.api.app.context import ContextManager


def test_can_create_incident_memory():
    memory = IncidentMemory(
        service="order-service",
        symptom="订单接口 500",
        root_cause="配置超时过短",
        fix="调整 payment.timeout",
        confidence=0.8,
        source_run_id="run-1",
        evidence_refs=["ev_log_001"],
    )

    assert memory.memory_id.startswith("mem_")
    assert memory.service == "order-service"
    assert memory.evidence_refs == ["ev_log_001"]


def test_memory_store_add_list_get(tmp_path):
    store = MemoryStore(tmp_path / "incidents.json")
    memory = IncidentMemory(
        memory_id="mem-1",
        service="order-service",
        symptom="订单接口 500",
        root_cause="日志异常",
        fix="查看 trace_id",
        source_run_id="run-1",
        evidence_refs=["ev_log_001"],
    )

    store.add(memory)

    assert len(store.list()) == 1
    assert store.get("mem-1").root_cause == "日志异常"
    assert store.get("missing") is None


def test_same_service_retrieves_memory(tmp_path):
    store = MemoryStore(tmp_path / "incidents.json")
    store.add(IncidentMemory(
        service="order-service",
        symptom="订单接口 500",
        root_cause="配置差异",
        fix="同步 prod 配置",
        source_run_id="run-1",
        evidence_refs=["ev_config_001"],
    ))

    results = store.query_by_service_or_symptom("库存接口报错", service="order-service")

    assert len(results) == 1
    assert results[0].match_reason == "service_exact_match"
    assert results[0].freshness_status == "fresh"


def test_query_keywords_retrieve_similar_symptom(tmp_path):
    store = MemoryStore(tmp_path / "incidents.json")
    store.add(IncidentMemory(
        service="payment-service",
        symptom="订单支付接口 timeout",
        root_cause="下游支付服务超时",
        fix="增加重试并检查下游",
        source_run_id="run-1",
        evidence_refs=["ev_log_001"],
    ))

    results = store.query_by_service_or_symptom("订单支付 timeout 怎么排查")

    assert len(results) == 1
    assert results[0].match_reason == "symptom_keyword_match"


def test_old_memory_is_marked_stale():
    old_date = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
    memory = IncidentMemory(
        service="order-service",
        symptom="订单接口 500",
        root_cause="历史原因",
        fix="历史修复",
        source_run_id="run-1",
        evidence_refs=["ev_log_001"],
        created_at=old_date,
    )

    freshness = evaluate_freshness(memory, ttl_days=30)

    assert freshness.freshness_status == "stale"


def test_missing_source_or_evidence_is_marked_weak():
    memory = IncidentMemory(
        service="order-service",
        symptom="订单接口 500",
        root_cause="历史原因",
        fix="历史修复",
    )

    freshness = evaluate_freshness(memory)

    assert freshness.freshness_status == "weak"


def test_context_package_includes_incident_memory_section(tmp_path):
    store = MemoryStore(tmp_path / "incidents.json")
    store.add(IncidentMemory(
        service="order-service",
        symptom="订单接口 500",
        root_cause="配置差异",
        fix="同步配置",
        source_run_id="run-1",
        evidence_refs=["ev_config_001"],
    ))

    package = ContextManager(memory_store=store).build(
        query="为什么 order-service 订单接口 500？",
        route={"type": "complex_troubleshooting"},
        plan={"steps": []},
        tool_results=[],
        trace_summary={},
    )

    section = package.section("incident_memory")
    assert section is not None
    assert "配置差异" in section.content
    assert package.metadata.memory_hit_count == 1
    assert package.metadata.fresh_memory_count == 1


def test_answer_synthesizer_marks_memory_as_historical_reference(tmp_path):
    store = MemoryStore(tmp_path / "incidents.json")
    store.add(IncidentMemory(
        service="order-service",
        symptom="订单接口 500",
        root_cause="历史配置差异",
        fix="同步配置",
        source_run_id="run-1",
        evidence_refs=["ev_config_001"],
    ))
    context_package = ContextManager(memory_store=store).build(
        query="为什么 order-service 订单接口 500？",
        route={"type": "complex_troubleshooting"},
        plan={"steps": []},
        tool_results=[],
        trace_summary={},
    )

    synthesis = AnswerSynthesizer().synthesize(
        query="为什么 order-service 订单接口 500？",
        route=RouterResult(type="complex_troubleshooting", intent="log_analysis", confidence=0.8, reason="test"),
        plan=Plan(plan_type="troubleshooting_plan", task_type="log_analysis", steps=[]),
        tool_results=[],
        use_llm=False,
        context_package=context_package,
    )

    assert "历史参考" in synthesis["answer"]
    assert "不是当前证据" in synthesis["answer"]
    assert "当前证据不足" in synthesis["answer"]


def test_llm_disabled_full_chain_writes_memory(monkeypatch, tmp_path):
    monkeypatch.setenv("INCIDENT_MEMORY_FILE", str(tmp_path / "incidents.json"))
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-v4-flash")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")
    monkeypatch.setenv("LLM_ENABLED", "false")

    data = chat_endpoint(ChatRequest(query="为什么订单接口报500？")).model_dump()
    memory_step = [step for step in data["trace"]["steps"] if step["stage"] == "memory"][0]

    assert data["answer_source"] == "fallback"
    assert memory_step["memory_created"] is True
    assert memory_step["memory_id"]
    assert len(MemoryStore(tmp_path / "incidents.json").list()) == 1
