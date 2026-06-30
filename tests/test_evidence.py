from app.api.chat import chat_endpoint
from app.core.models import ChatRequest
from app.evidence import EvidenceChainBuilder


def _tool_result(tool_name: str, **overrides):
    data = {
        "tool": tool_name,
        "tool_name": tool_name,
        "status": "success",
        "result": f"{tool_name} result",
        "confidence": 0.82,
        "source": f"data/{tool_name}",
        "documents": [],
        "error": "",
    }
    data.update(overrides)
    return data


def _payload(tool_results):
    return {
        "query": "为什么订单接口报500？",
        "route": {"type": "complex_troubleshooting", "confidence": 0.9, "reason": "troubleshooting"},
        "plan": {"plan_type": "troubleshooting_plan", "steps": []},
        "tool_results": tool_results,
        "trace": {"steps": []},
        "answer": "初步判断：日志和配置证据指向 timeout。",
        "evaluation": {"overall_score": 0.8, "issues": [], "suggestions": []},
    }


def test_log_tool_result_generates_log_evidence():
    chain = EvidenceChainBuilder().build(_payload([_tool_result("log_tool")]))

    assert chain.evidence_items[0].type == "log"
    assert chain.evidence_items[0].related_tool == "log_tool"


def test_config_tool_result_generates_config_evidence():
    chain = EvidenceChainBuilder().build(_payload([_tool_result("config_tool")]))

    assert chain.evidence_items[0].type == "config"
    assert chain.evidence_items[0].related_tool == "config_tool"


def test_git_tool_result_generates_git_evidence():
    chain = EvidenceChainBuilder().build(_payload([_tool_result("git_tool")]))

    assert chain.evidence_items[0].type == "git"
    assert chain.evidence_items[0].related_tool == "git_tool"


def test_rag_retriever_result_generates_rag_evidence():
    chain = EvidenceChainBuilder().build(
        _payload([
            _tool_result(
                "rag_retriever",
                documents=[{"source": "data/docs/troubleshooting.md", "score": 0.9}],
            )
        ])
    )

    assert chain.evidence_items[0].type == "rag"
    assert "知识库检索到 1 条相关片段" in chain.evidence_items[0].summary


def test_complex_troubleshooting_generates_root_cause_candidates():
    chain = EvidenceChainBuilder().build(
        _payload([
            _tool_result("log_tool", result="日志出现 timeout 和 500"),
            _tool_result("config_tool", result="prod payment.timeout 小于 dev"),
        ])
    )

    assert chain.root_cause_candidates
    candidate = chain.root_cause_candidates[0]
    assert candidate.confidence >= 0.85
    assert {"ev_log_001", "ev_config_001"}.issubset(set(candidate.supporting_evidence_ids))


def test_overall_confidence_is_between_zero_and_one():
    chain = EvidenceChainBuilder().build(_payload([_tool_result("log_tool")]))

    assert 0 <= chain.overall_confidence <= 1


def test_failed_tool_does_not_generate_high_confidence_evidence():
    chain = EvidenceChainBuilder().build(
        _payload([
            _tool_result(
                "log_tool",
                status="failed",
                result="",
                confidence=0.95,
                error="file_not_found",
            )
        ])
    )

    log_evidence = [item for item in chain.evidence_items if item.type == "log"][0]
    assert log_evidence.confidence <= 0.3


def test_chat_returns_evidence_chain_and_trace_stage(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "false")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    data = chat_endpoint(ChatRequest(query="为什么订单接口报500？")).model_dump()

    assert data["llm_used"] is False
    assert data["evidence_chain"] is not None
    assert 0 <= data["evidence_chain"]["overall_confidence"] <= 1
    assert data["evidence_chain"]["evidence_items"]

    evidence_step = [step for step in data["trace"]["steps"] if step["stage"] == "evidence"][0]
    assert evidence_step["engine"] == "rule_based"
    assert evidence_step["evidence_count"] == len(data["evidence_chain"]["evidence_items"])
