from apps.api.app.rag.embedding_provider import LocalHashEmbeddingProvider, get_embedding_provider
from apps.api.app.rag.rerank_provider import get_rerank_provider
from apps.api.app.rag.retriever import KeywordRetriever


def test_v080_local_embedding_provider_is_deterministic():
    provider = LocalHashEmbeddingProvider()

    first = provider.embed_query("服务启动失败 port already in use")
    second = provider.embed_query("服务启动失败 port already in use")

    assert first == second
    assert first
    assert abs(sum(value * value for value in first.values()) - 1.0) < 0.0001


def test_v080_embedding_provider_falls_back_without_external_key(monkeypatch):
    monkeypatch.setenv("RAG_EMBEDDING_PROVIDER", "openai_compatible")
    monkeypatch.delenv("RAG_EMBEDDING_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    provider, fallback_used, reason = get_embedding_provider()

    assert provider.name == "local"
    assert fallback_used is True
    assert reason == "embedding_api_key_missing"


def test_v080_rerank_provider_falls_back_without_external_key(monkeypatch):
    monkeypatch.setenv("RAG_RERANK_PROVIDER", "openai_compatible")
    monkeypatch.delenv("RAG_RERANK_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    provider, fallback_used, reason = get_rerank_provider()

    assert provider.name == "local"
    assert fallback_used is True
    assert reason == "rerank_api_key_missing"


def test_v080_retriever_records_provider_metadata():
    result = KeywordRetriever().retrieve_with_evidence("nginx 502 upstream", top_k=3)

    assert result["embedding_provider"] == "local"
    assert result["embedding_fallback_used"] is False
    assert result["rerank_provider"] == "local"
    assert result["rerank_fallback_used"] is False
    assert result["retrieved_chunks"]


def test_v080_retriever_falls_back_when_external_embedding_errors(monkeypatch):
    monkeypatch.setenv("RAG_EMBEDDING_PROVIDER", "openai_compatible")
    monkeypatch.setenv("RAG_EMBEDDING_API_KEY", "test-key")
    monkeypatch.setenv("RAG_EMBEDDING_MODEL", "test-embedding-model")

    result = KeywordRetriever().retrieve_with_evidence("port already in use 服务启动失败", top_k=3)

    assert result["retrieved_chunks"]
    assert result["embedding_provider"] == "local"
    assert result["embedding_fallback_used"] is True
    assert result["embedding_fallback_reason"].startswith("embedding_provider_error:")


def test_v080_retriever_falls_back_when_external_rerank_errors(monkeypatch):
    monkeypatch.setenv("RAG_RERANK_PROVIDER", "openai_compatible")
    monkeypatch.setenv("RAG_RERANK_API_KEY", "test-key")
    monkeypatch.setenv("RAG_RERANK_MODEL", "test-rerank-model")

    result = KeywordRetriever().retrieve_with_evidence("nginx 502 upstream", top_k=3)

    assert result["retrieved_chunks"]
    assert result["rerank_provider"] == "local"
    assert result["rerank_fallback_used"] is True
    assert result["rerank_fallback_reason"].startswith("rerank_provider_error:")

