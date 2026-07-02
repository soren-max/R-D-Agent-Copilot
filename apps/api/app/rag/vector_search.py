"""Deterministic local vector-style retrieval without external dependencies."""

from __future__ import annotations

from dataclasses import dataclass

from apps.api.app.rag.chunker import KnowledgeChunk, extract_keywords
from apps.api.app.rag.keyword_search import SearchHit


@dataclass(frozen=True)
class VectorSearchIndex:
    chunks: list[KnowledgeChunk]

    def search(self, query: str, top_k: int = 3) -> list[SearchHit]:
        query_vector = _hash_vector(extract_keywords(query))
        if not query_vector:
            return []

        hits: list[SearchHit] = []
        for chunk in self.chunks:
            chunk_vector = _hash_vector(chunk.keywords)
            score = _cosine(query_vector, chunk_vector)
            if score <= 0:
                continue
            hits.append(SearchHit(chunk=chunk, score=round(score, 4), retrieval_type="vector"))

        hits.sort(key=lambda hit: (-hit.score, hit.chunk.source, hit.chunk.chunk_id))
        return hits[:top_k]


def _hash_vector(tokens: list[str], buckets: int = 128) -> dict[int, float]:
    vector: dict[str, float] = {}
    for token in tokens:
        vector[token] = vector.get(token, 0.0) + 1.0
    return vector


def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    dot = sum(value * right.get(index, 0.0) for index, value in left.items())
    if dot <= 0:
        return 0.0
    left_norm = sum(value * value for value in left.values()) ** 0.5
    right_norm = sum(value * value for value in right.values()) ** 0.5
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return min(1.0, dot / (left_norm * right_norm))
