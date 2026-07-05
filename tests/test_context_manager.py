from app.api.chat import chat_endpoint
from app.core.models import ChatRequest
from apps.api.app.context import ContextManager


def test_current_query_is_not_trimmed():
    query = "为什么订单服务持续报错？" * 200
    package = ContextManager(tool_budget=80, rag_budget=80, history_budget=80).build(
        query=query,
        route={"type": "complex_troubleshooting"},
        plan={"steps": []},
        tool_results=[],
        trace_summary={"steps": []},
    )

    assert package.section("current_query").content == query
    assert "current_query" not in package.metadata.reduced_sections


def test_tiny_total_budget_keeps_current_query_even_when_total_exceeds_budget():
    query = "用户原始问题必须完整保留。" * 100
    package = ContextManager(
        tool_budget=80,
        rag_budget=80,
        history_budget=80,
        total_budget=120,
    ).build(
        query=query,
        route={"type": "complex_troubleshooting", "intent": "log_analysis", "confidence": 0.9},
        plan={"steps": [{"tool": "log_tool", "action": "query_logs"}]},
        tool_results=[{
            "tool": "log_tool",
            "status": "success",
            "result": "ERROR timeout 500\n" * 80,
        }],
        trace_summary={"steps": [{"stage": "executor", "output": "x" * 500}]},
    )

    assert package.section("current_query").content == query
    # current_query is protected, so tiny total budgets are allowed to be exceeded.
    assert package.metadata.total_chars_after > 120


def test_long_log_output_is_summarized():
    long_log = "\n".join(
        [f"INFO heartbeat {index}" for index in range(300)]
        + ["ERROR order-service timeout 500"]
        + [f"INFO cleanup {index}" for index in range(300)]
    )
    package = ContextManager(tool_budget=360, rag_budget=80, history_budget=80).build(
        query="为什么订单接口报500？",
        route={"type": "complex_troubleshooting"},
        plan={"steps": [{"tool": "log_tool"}]},
        tool_results=[{
            "tool": "log_tool",
            "status": "success",
            "source": "local_sample",
            "confidence": 0.9,
            "result": long_log,
        }],
        trace_summary={"steps": []},
    )

    tool_section = package.section("tool_evidence")
    assert "ERROR order-service timeout 500" in tool_section.content
    assert "已压缩" in tool_section.content or "已省略" in tool_section.content
    assert "tool_evidence" in package.metadata.reduced_sections


def test_metadata_records_compression_ratio():
    package = ContextManager(tool_budget=220, rag_budget=120, history_budget=120).build(
        query="为什么订单接口报500？",
        route={"type": "complex_troubleshooting"},
        plan={"steps": [{"tool": "log_tool"}]},
        tool_results=[{
            "tool": "log_tool",
            "status": "success",
            "result": "ERROR timeout 500\n" * 200,
        }],
        trace_summary={"steps": [{"stage": "executor", "output": "x" * 1000}]},
    )

    metadata = package.metadata
    assert metadata.total_chars_before > metadata.total_chars_after
    assert 0 < metadata.compression_ratio < 1
    assert metadata.section_char_counts["tool_evidence"] == len(package.section("tool_evidence").content)
    assert metadata.reduced_sections


def test_empty_evidence_does_not_fail():
    package = ContextManager().build(
        query="什么是配置中心？",
        route={"type": "simple_qa"},
        plan={"steps": []},
        tool_results=[],
        trace_summary={},
    )

    assert package.section("tool_evidence").content == "[]"
    assert package.section("rag_evidence").content == "[]"
    assert package.metadata.total_chars_after > 0


def test_long_rag_evidence_is_summarized_and_keeps_source_title():
    package = ContextManager(tool_budget=120, rag_budget=760, history_budget=120).build(
        query="订单接口 500 怎么排查？",
        route={"type": "complex_troubleshooting"},
        plan={"steps": [{"tool": "rag_retriever"}]},
        tool_results=[{
            "tool": "rag_retriever",
            "status": "success",
            "documents": [{
                "source": "service-logs.md",
                "title": "订单接口 500 排查",
                "chunk_id": "service-logs:001",
                "score": 0.91,
                "content": "先检查 ERROR 日志、trace_id、下游 timeout 和配置变更。" * 120,
            }],
            "rag_metadata": {
                "grounding_status": "grounded",
                "evidence": [{
                    "source": "service-logs.md",
                    "title": "订单接口 500 排查",
                    "content_excerpt": "检查 ERROR 日志和 trace_id。",
                }],
            },
        }],
        trace_summary={},
    )

    rag_section = package.section("rag_evidence")
    assert "service-logs.md" in rag_section.content
    assert "订单接口 500 排查" in rag_section.content
    assert "已压缩" in rag_section.content
    assert "rag_evidence" in package.metadata.reduced_sections


def test_small_budget_rag_documents_keep_metadata_for_each_doc():
    package = ContextManager(tool_budget=80, rag_budget=180, history_budget=80, total_budget=900).build(
        query="订单接口 500 怎么排查？",
        route={"type": "complex_troubleshooting"},
        plan={"steps": [{"tool": "rag_retriever"}]},
        tool_results=[{
            "tool": "rag_retriever",
            "status": "success",
            "documents": [
                {
                    "source": "service-logs.md",
                    "title": "日志排查",
                    "chunk_id": "logs:001",
                    "score": 0.91,
                    "content": "ERROR 日志 trace_id timeout " * 80,
                },
                {
                    "source": "order-service-faq.md",
                    "title": "订单服务 FAQ",
                    "chunk_id": "faq:002",
                    "score": 0.82,
                    "content": "订单接口 500 常见原因 " * 80,
                },
            ],
            "rag_metadata": {"grounding_status": "grounded"},
        }],
        trace_summary={},
    )

    rag_content = package.section("rag_evidence").content
    assert "service-logs.md" in rag_content or "日志排查" in rag_content
    assert "order-service-faq.md" in rag_content or "订单服务 FAQ" in rag_content
    assert "0.91" in rag_content
    assert "0.82" in rag_content


def test_context_metadata_is_written_to_synthesizer_trace(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-v4-flash")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")
    monkeypatch.setenv("LLM_ENABLED", "false")

    data = chat_endpoint(ChatRequest(query="什么是配置中心？")).model_dump()
    synthesizer_step = [step for step in data["trace"]["steps"] if step["stage"] == "synthesizer"][0]

    metadata = synthesizer_step["context_metadata"]
    assert metadata["total_chars_before"] >= metadata["total_chars_after"]
    assert "current_query" in metadata["section_char_counts"]
