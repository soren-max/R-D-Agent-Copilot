"""Rerank provider abstraction with deterministic local fallback."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Protocol

from apps.api.app.rag.keyword_search import SearchHit
from apps.api.app.rag.reranker import LocalReranker
from apps.api.app.rag.schemas import RerankResult

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None


class RerankProvider(Protocol):
    name: str
    model: str

    def rerank(self, query: str, hits: list[SearchHit], top_k: int = 5) -> tuple[list[SearchHit], list[RerankResult]]:
        """Return reranked hits and explainable rerank records."""


@dataclass(frozen=True)
class RerankSettings:
    provider: str = "local"
    model: str = "local-overlap-reranker"
    base_url: str = ""
    timeout_seconds: float = 10.0
    api_key_configured: bool = False
    api_key: str = field(default="", repr=False)
    external_calls_enabled: bool = False


class LocalRerankProvider:
    name = "local"
    model = "local-overlap-reranker"

    def __init__(self) -> None:
        self._reranker = LocalReranker()

    def rerank(self, query: str, hits: list[SearchHit], top_k: int = 5) -> tuple[list[SearchHit], list[RerankResult]]:
        return self._reranker.rerank(query, hits, top_k=top_k)


class OpenAICompatibleRerankProvider:
    """OpenAI-compatible rerank provider with local fallback at caller level."""

    name = "openai_compatible"

    def __init__(self, settings: RerankSettings) -> None:
        self.settings = settings
        self.model = settings.model

    def rerank(self, query: str, hits: list[SearchHit], top_k: int = 5) -> tuple[list[SearchHit], list[RerankResult]]:
        if not self.settings.external_calls_enabled:
            raise RuntimeError("RAG_EXTERNAL_CALLS_ENABLED is not true.")
        if OpenAI is None:
            raise RuntimeError("OpenAI SDK is not installed.")
        if not self.settings.api_key:
            raise RuntimeError("RAG_RERANK_API_KEY or LLM_API_KEY is required.")
        if not hits:
            return [], []

        client = OpenAI(
            api_key=self.settings.api_key,
            base_url=self.settings.base_url or None,
            timeout=self.settings.timeout_seconds,
        )
        items = [
            {
                "chunk_id": hit.chunk.chunk_id,
                "source": hit.chunk.source,
                "title": hit.chunk.title,
                "score": hit.score,
                "content": hit.chunk.content[:500],
            }
            for hit in hits[:20]
        ]
        response = client.chat.completions.create(
            model=self.settings.model,
            messages=[
                {
                    "role": "system",
                    "content": "Return JSON only: {\"ordered_chunk_ids\": [\"...\"]}. Rank chunks by usefulness for troubleshooting.",
                },
                {"role": "user", "content": json.dumps({"query": query, "chunks": items}, ensure_ascii=False)},
            ],
        )
        content = response.choices[0].message.content or "{}"
        ordered_ids = json.loads(content).get("ordered_chunk_ids", [])
        hit_by_id = {hit.chunk.chunk_id: hit for hit in hits}
        ordered_hits = [hit_by_id[chunk_id] for chunk_id in ordered_ids if chunk_id in hit_by_id]
        ordered_hits.extend(hit for hit in hits if hit.chunk.chunk_id not in set(ordered_ids))
        selected = ordered_hits[:top_k]
        results = [
            RerankResult(
                chunk_id=hit.chunk.chunk_id,
                source=hit.chunk.source,
                original_score=hit.score,
                rerank_score=round(max(0.0, 1.0 - index * 0.05), 4),
                final_score=round(max(hit.score, 1.0 - index * 0.05), 4),
                reason="external_rerank_provider",
            )
            for index, hit in enumerate(selected)
        ]
        final_hits = [
            SearchHit(hit.chunk, results[index].final_score, hit.retrieval_type)
            for index, hit in enumerate(selected)
        ]
        return final_hits, results


def get_rerank_settings() -> RerankSettings:
    provider = os.getenv("RAG_RERANK_PROVIDER", "local").strip().lower() or "local"
    model = os.getenv("RAG_RERANK_MODEL", "local-overlap-reranker")
    api_key = os.getenv("RAG_RERANK_API_KEY") or os.getenv("LLM_API_KEY", "")
    try:
        timeout_seconds = float(os.getenv("RAG_PROVIDER_TIMEOUT_SECONDS", "10"))
    except ValueError:
        timeout_seconds = 10.0
    return RerankSettings(
        provider=provider,
        model=model,
        base_url=os.getenv("RAG_RERANK_BASE_URL", os.getenv("LLM_BASE_URL", "")),
        timeout_seconds=timeout_seconds,
        api_key_configured=bool(api_key),
        api_key=api_key,
        external_calls_enabled=os.getenv("RAG_EXTERNAL_CALLS_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"},
    )


def get_rerank_provider(settings: RerankSettings | None = None) -> tuple[RerankProvider, bool, str]:
    settings = settings or get_rerank_settings()
    if settings.provider == "local":
        return LocalRerankProvider(), False, ""
    if not settings.api_key_configured:
        return LocalRerankProvider(), True, "rerank_api_key_missing"
    return OpenAICompatibleRerankProvider(settings), False, ""
