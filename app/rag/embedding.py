"""Deterministic local embeddings for RAG vector retrieval."""

from __future__ import annotations

from app.rag.vector_store import embed_text as _embed_text


def embed_text(text: str) -> list[float]:
    """Return a stable token-hashing embedding without external model calls."""
    return _embed_text(text)
