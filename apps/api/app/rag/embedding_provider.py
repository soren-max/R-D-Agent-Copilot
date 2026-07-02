"""Embedding provider abstraction for local and future production RAG."""

from __future__ import annotations

import math
import os
from collections import Counter
from dataclasses import dataclass, field
from typing import Protocol

from apps.api.app.rag.chunker import extract_keywords

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None


SparseVector = dict[str, float]


class EmbeddingProvider(Protocol):
    name: str
    model: str

    def embed_query(self, text: str) -> SparseVector:
        """Embed a query into the local sparse-vector contract."""

    def embed_document(self, text: str, keywords: list[str]) -> SparseVector:
        """Embed a chunk into the local sparse-vector contract."""


@dataclass(frozen=True)
class EmbeddingSettings:
    provider: str = "local"
    model: str = "local-keyword-hash"
    base_url: str = ""
    timeout_seconds: float = 10.0
    api_key_configured: bool = False
    api_key: str = field(default="", repr=False)
    external_calls_enabled: bool = False


class LocalHashEmbeddingProvider:
    name = "local"
    model = "local-keyword-hash"

    def embed_query(self, text: str) -> SparseVector:
        return _normalize_counts(extract_keywords(text))

    def embed_document(self, text: str, keywords: list[str]) -> SparseVector:
        tokens = keywords or extract_keywords(text)
        return _normalize_counts(tokens)


class OpenAICompatibleEmbeddingProvider:
    """OpenAI-compatible embedding provider with local fallback at caller level."""

    name = "openai_compatible"

    def __init__(self, settings: EmbeddingSettings) -> None:
        self.settings = settings
        self.model = settings.model

    def embed_query(self, text: str) -> SparseVector:
        return self._embed(text)

    def embed_document(self, text: str, keywords: list[str]) -> SparseVector:
        return self._embed(text)

    def _embed(self, text: str) -> SparseVector:
        if not self.settings.external_calls_enabled:
            raise RuntimeError("RAG_EXTERNAL_CALLS_ENABLED is not true.")
        if OpenAI is None:
            raise RuntimeError("OpenAI SDK is not installed.")
        if not self.settings.api_key:
            raise RuntimeError("RAG_EMBEDDING_API_KEY or LLM_API_KEY is required.")
        client = OpenAI(
            api_key=self.settings.api_key,
            base_url=self.settings.base_url or None,
            timeout=self.settings.timeout_seconds,
        )
        response = client.embeddings.create(model=self.settings.model, input=text)
        embedding = response.data[0].embedding
        return {str(index): float(value) for index, value in enumerate(embedding) if value}


def get_embedding_settings() -> EmbeddingSettings:
    provider = os.getenv("RAG_EMBEDDING_PROVIDER", "local").strip().lower() or "local"
    model = os.getenv("RAG_EMBEDDING_MODEL", "local-keyword-hash")
    api_key = os.getenv("RAG_EMBEDDING_API_KEY") or os.getenv("LLM_API_KEY", "")
    try:
        timeout_seconds = float(os.getenv("RAG_PROVIDER_TIMEOUT_SECONDS", "10"))
    except ValueError:
        timeout_seconds = 10.0
    return EmbeddingSettings(
        provider=provider,
        model=model,
        base_url=os.getenv("RAG_EMBEDDING_BASE_URL", os.getenv("LLM_BASE_URL", "")),
        timeout_seconds=timeout_seconds,
        api_key_configured=bool(api_key),
        api_key=api_key,
        external_calls_enabled=os.getenv("RAG_EXTERNAL_CALLS_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"},
    )


def get_embedding_provider(settings: EmbeddingSettings | None = None) -> tuple[EmbeddingProvider, bool, str]:
    settings = settings or get_embedding_settings()
    if settings.provider == "local":
        return LocalHashEmbeddingProvider(), False, ""
    if not settings.api_key_configured:
        return LocalHashEmbeddingProvider(), True, "embedding_api_key_missing"
    return OpenAICompatibleEmbeddingProvider(settings), False, ""


def _normalize_counts(tokens: list[str]) -> SparseVector:
    if not tokens:
        return {}
    counts = Counter(tokens)
    norm = math.sqrt(sum(value * value for value in counts.values()))
    if norm == 0:
        return {}
    return {token: value / norm for token, value in counts.items()}
