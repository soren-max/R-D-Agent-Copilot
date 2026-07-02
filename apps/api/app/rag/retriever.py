"""v0.3.x query rewrite + hybrid retriever."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from apps.api.app.rag.chunker import chunk_documents
from apps.api.app.rag.evidence import build_evidence
from apps.api.app.rag.embedding_provider import EmbeddingSettings, get_embedding_provider, get_embedding_settings
from apps.api.app.rag.grounding import evaluate_grounding
from apps.api.app.rag.keyword_search import KeywordSearchIndex, SearchHit
from apps.api.app.rag.loader import KB_DIR, load_markdown_documents
from apps.api.app.rag.query_rewrite import rewrite_query
from apps.api.app.rag.rerank_provider import RerankSettings, get_rerank_provider, get_rerank_settings
from apps.api.app.rag.vector_search import VectorSearchIndex


class KeywordRetriever:
    def __init__(self, kb_dir: Path | None = None):
        self.kb_dir = kb_dir or KB_DIR
        self._hits_cache: dict[tuple[str, int, str, bool], list[SearchHit]] = {}
        self._embedding_provider, self._embedding_fallback_used, self._embedding_fallback_reason = get_embedding_provider()
        self._rerank_provider, self._rerank_fallback_used, self._rerank_fallback_reason = get_rerank_provider()

    def chunks(self):
        return chunk_documents(load_markdown_documents(self.kb_dir))

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        retrieval_type: str = "hybrid",
        use_query_rewrite: bool = True,
    ) -> list[dict[str, Any]]:
        """Return relevant chunk dictionaries. No matches returns an empty list."""

        hits = self.search(query, top_k=top_k, retrieval_type=retrieval_type, use_query_rewrite=use_query_rewrite)
        reranked_hits, _ = self._rerank(query, hits, top_k)
        return [
            {
                **hit.chunk.to_dict(score=hit.score),
                "retrieval_type": hit.retrieval_type,
            }
            for hit in reranked_hits
        ]

    def search(
        self,
        query: str,
        top_k: int = 3,
        retrieval_type: str = "hybrid",
        use_query_rewrite: bool = True,
    ) -> list[SearchHit]:
        if retrieval_type not in {"keyword", "vector", "hybrid"}:
            raise ValueError("retrieval_type must be keyword, vector, or hybrid")
        cache_key = (query, top_k, retrieval_type, use_query_rewrite)
        if cache_key not in self._hits_cache:
            chunks = self.chunks()
            keyword_index = KeywordSearchIndex(chunks)
            vector_index = VectorSearchIndex(chunks, embedding_provider=self._embedding_provider)
            rewrite = rewrite_query(query)
            search_queries = rewrite.all_queries() if use_query_rewrite else [query]
            keyword_hits: list[SearchHit] = []
            vector_hits: list[SearchHit] = []
            for rewritten_query in search_queries:
                if retrieval_type in {"keyword", "hybrid"}:
                    keyword_hits.extend(keyword_index.search(rewritten_query, top_k=top_k * 2))
                if retrieval_type in {"vector", "hybrid"}:
                    try:
                        vector_hits.extend(vector_index.search(rewritten_query, top_k=top_k * 2))
                    except Exception as exc:
                        self._embedding_provider, _, _ = get_embedding_provider(EmbeddingSettings(provider="local"))
                        self._embedding_fallback_used = True
                        self._embedding_fallback_reason = f"embedding_provider_error:{type(exc).__name__}"
                        vector_index = VectorSearchIndex(chunks, embedding_provider=self._embedding_provider)
                        vector_hits.extend(vector_index.search(rewritten_query, top_k=top_k * 2))
            self._hits_cache[cache_key] = _merge_hits(keyword_hits, vector_hits, top_k)
        return self._hits_cache[cache_key]

    def retrieve_with_evidence(
        self,
        query: str,
        top_k: int = 3,
        retrieval_type: str = "hybrid",
        use_query_rewrite: bool = True,
    ) -> dict[str, Any]:
        rewrite = rewrite_query(query)
        hits = self.search(query, top_k=top_k, retrieval_type=retrieval_type, use_query_rewrite=use_query_rewrite)
        reranked_hits, rerank_results = self._rerank(query, hits, top_k)
        chunks = [
            {
                **hit.chunk.to_dict(score=hit.score),
                "retrieval_type": hit.retrieval_type,
            }
            for hit in reranked_hits
        ]
        evidence = build_evidence(reranked_hits)
        grounding = evaluate_grounding(evidence)
        return {
            "query": query,
            "rewritten_queries": rewrite.all_queries() if use_query_rewrite else [query],
            "query_expansions": rewrite.expansions if use_query_rewrite else [],
            "retrieved_chunks": chunks,
            "rerank_results": [item.model_dump() for item in rerank_results],
            "evidence": [item.to_dict() for item in evidence],
            "grounding_status": grounding.grounding_status,
            "no_evidence_reason": grounding.no_evidence_reason,
            "retrieved_count": len(chunks),
            "retrieval_top_k": top_k,
            "retrieval_type": retrieval_type,
            "keyword_hit_count": sum(1 for hit in hits if hit.retrieval_type in {"keyword", "hybrid"}),
            "vector_hit_count": sum(1 for hit in hits if hit.retrieval_type in {"vector", "hybrid"}),
            "embedding_provider": self._embedding_provider.name,
            "embedding_model": self._embedding_provider.model,
            "embedding_fallback_used": self._embedding_fallback_used,
            "embedding_fallback_reason": self._embedding_fallback_reason,
            "rerank_provider": self._rerank_provider.name,
            "rerank_model": self._rerank_provider.model,
            "rerank_fallback_used": self._rerank_fallback_used,
            "rerank_fallback_reason": self._rerank_fallback_reason,
        }

    def provider_status(self) -> dict[str, Any]:
        embedding_settings = get_embedding_settings()
        rerank_settings = get_rerank_settings()
        return {
            "embedding_provider_configured": embedding_settings.provider,
            "embedding_provider_active": self._embedding_provider.name,
            "embedding_model": self._embedding_provider.model,
            "embedding_fallback_used": self._embedding_fallback_used,
            "embedding_fallback_reason": self._embedding_fallback_reason,
            "rerank_provider_configured": rerank_settings.provider,
            "rerank_provider_active": self._rerank_provider.name,
            "rerank_model": self._rerank_provider.model,
            "rerank_fallback_used": self._rerank_fallback_used,
            "rerank_fallback_reason": self._rerank_fallback_reason,
        }

    def _rerank(
        self,
        query: str,
        hits: list[SearchHit],
        top_k: int,
    ) -> tuple[list[SearchHit], list[Any]]:
        try:
            return self._rerank_provider.rerank(query, hits, top_k=top_k)
        except Exception as exc:
            self._rerank_provider, _, _ = get_rerank_provider(RerankSettings(provider="local"))
            self._rerank_fallback_used = True
            self._rerank_fallback_reason = f"rerank_provider_error:{type(exc).__name__}"
            return self._rerank_provider.rerank(query, hits, top_k=top_k)


def _merge_hits(keyword_hits: list[SearchHit], vector_hits: list[SearchHit], top_k: int) -> list[SearchHit]:
    merged: dict[str, SearchHit] = {}
    for hit in keyword_hits + vector_hits:
        existing = merged.get(hit.chunk.chunk_id)
        if existing is None:
            merged[hit.chunk.chunk_id] = hit
            continue
        combined_score = min(1.0, max(existing.score, hit.score) + min(existing.score, hit.score) * 0.2)
        retrieval_type = existing.retrieval_type
        if retrieval_type != hit.retrieval_type:
            retrieval_type = "hybrid"
        merged[hit.chunk.chunk_id] = SearchHit(hit.chunk, round(combined_score, 4), retrieval_type)

    hits = list(merged.values())
    hits.sort(key=lambda hit: (-hit.score, hit.chunk.source, hit.chunk.chunk_id))
    return hits[:top_k]
