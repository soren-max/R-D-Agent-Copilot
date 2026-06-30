from pathlib import Path

from app.rag.retriever import LocalKnowledgeRetriever


def test_ingestion_generates_chunks_with_metadata():
    chunks = LocalKnowledgeRetriever().ingest()

    assert chunks
    first = chunks[0]
    assert first.content
    assert first.source.startswith("data/docs/")
    assert first.title
    assert first.section
    assert first.chunk_id
    assert first.doc_type == "markdown"
    assert first.updated_at


def test_retriever_loads_markdown_documents():
    result = LocalKnowledgeRetriever().retrieve("配置中心", top_k=3)

    assert "error" not in result
    assert result["query"] == "配置中心"
    assert result["documents"]
    assert all(doc["source"].startswith("data/docs/") for doc in result["documents"])
    assert result["grounding_status"] == "grounded"


def test_retriever_returns_config_center_for_config_query():
    result = LocalKnowledgeRetriever().retrieve("什么是配置中心？", top_k=3)

    assert result["documents"]
    assert result["documents"][0]["source"] == "data/docs/config-center.md"
    assert "配置中心" in result["documents"][0]["content"]
    assert 0 < result["documents"][0]["score"] <= 1
    assert result["documents"][0]["chunk_id"]
    assert result["documents"][0]["retrieval_type"] in {"vector", "keyword", "hybrid"}


def test_vector_retrieval_returns_top_k_documents():
    result = LocalKnowledgeRetriever().retrieve("配置中心 timeout prod", top_k=2, retrieval_type="vector")

    assert len(result["documents"]) <= 2
    assert result["retrieval_type"] == "vector"
    assert result["documents"]


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

    assert result["query"] == "配置中心"
    assert result["documents"] == []
    assert result["error"] == "knowledge_base_not_found"
    assert result["grounding_status"] == "insufficient_evidence"


def test_retriever_returns_error_when_no_relevant_documents(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "sample.md").write_text("这里只包含完全无关的内容。", encoding="utf-8")

    result = LocalKnowledgeRetriever(docs_dir=docs_dir).retrieve("zzzz_unmatched_keyword")

    assert result["query"] == "zzzz_unmatched_keyword"
    assert result["documents"] == []
    assert result["error"] == "no_relevant_documents"
    assert result["grounding_status"] == "insufficient_evidence"


def test_keyword_retrieval_fallback_is_available():
    result = LocalKnowledgeRetriever().retrieve("trace_id 日志", top_k=3, retrieval_type="keyword")

    assert result["documents"]
    assert result["retrieval_type"] == "keyword"
    assert all(doc["retrieval_type"] == "keyword" for doc in result["documents"])


def test_score_threshold_filters_low_score_documents():
    result = LocalKnowledgeRetriever().retrieve("配置中心", top_k=3, score_threshold=1.01)

    assert result["documents"] == []
    assert result["grounding_status"] == "insufficient_evidence"


def test_metadata_filter_limits_results():
    result = LocalKnowledgeRetriever().retrieve(
        "timeout",
        top_k=5,
        metadata_filter={"source": "data/docs/order-service-faq.md"},
    )

    assert result["documents"]
    assert {doc["source"] for doc in result["documents"]} == {"data/docs/order-service-faq.md"}
