from pathlib import Path

from app.rag.retriever import LocalKnowledgeRetriever


def test_retriever_loads_markdown_documents():
    result = LocalKnowledgeRetriever().retrieve("配置中心", top_k=3)

    assert "error" not in result
    assert result["query"] == "配置中心"
    assert result["documents"]
    assert all(doc["source"].startswith("data/docs/") for doc in result["documents"])


def test_retriever_returns_config_center_for_config_query():
    result = LocalKnowledgeRetriever().retrieve("什么是配置中心？", top_k=3)

    assert result["documents"]
    assert result["documents"][0]["source"] == "data/docs/config-center.md"
    assert "配置中心" in result["documents"][0]["content"]
    assert 0 < result["documents"][0]["score"] <= 1


def test_retriever_returns_troubleshooting_docs_for_500_query():
    result = LocalKnowledgeRetriever().retrieve("接口 500 怎么排查", top_k=3)
    sources = {doc["source"] for doc in result["documents"]}

    assert sources & {
        "data/docs/troubleshooting-guide.md",
        "data/docs/order-service-faq.md",
    }


def test_retriever_returns_service_logs_for_trace_log_query():
    result = LocalKnowledgeRetriever().retrieve("trace_id 日志", top_k=3)

    assert result["documents"]
    assert result["documents"][0]["source"] == "data/docs/service-logs.md"
    assert "trace_id" in result["documents"][0]["content"]


def test_retriever_returns_error_when_knowledge_base_missing(tmp_path):
    missing_dir = tmp_path / "missing-docs"
    result = LocalKnowledgeRetriever(docs_dir=missing_dir).retrieve("配置中心")

    assert result == {
        "query": "配置中心",
        "documents": [],
        "error": "knowledge_base_not_found",
    }


def test_retriever_returns_error_when_no_relevant_documents(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "sample.md").write_text("这里只包含完全无关的内容。", encoding="utf-8")

    result = LocalKnowledgeRetriever(docs_dir=docs_dir).retrieve("zzzz_unmatched_keyword")

    assert result == {
        "query": "zzzz_unmatched_keyword",
        "documents": [],
        "error": "no_relevant_documents",
    }
