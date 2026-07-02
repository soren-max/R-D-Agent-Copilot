"""Lightweight deterministic reranker for retrieved chunks."""

from __future__ import annotations

from apps.api.app.rag.chunker import extract_keywords
from apps.api.app.rag.keyword_search import SearchHit
from apps.api.app.rag.schemas import RerankResult


class LocalReranker:
    """Rerank by query overlap, title/source signals, and original retrieval score."""

    def rerank(self, query: str, hits: list[SearchHit], top_k: int = 5) -> tuple[list[SearchHit], list[RerankResult]]:
        query_terms = set(extract_keywords(query))
        reranked: list[tuple[SearchHit, RerankResult]] = []
        for hit in hits:
            chunk_terms = set(hit.chunk.keywords)
            overlap = query_terms.intersection(chunk_terms)
            title_bonus = 0.08 if any(term in hit.chunk.title.lower() for term in query_terms) else 0.0
            source_bonus = 0.04 if any(term in hit.chunk.source.lower() for term in query_terms) else 0.0
            overlap_score = len(overlap) / max(1, len(query_terms))
            rerank_score = min(1.0, overlap_score + title_bonus + source_bonus)
            final_score = round(min(1.0, hit.score * 0.65 + rerank_score * 0.35), 4)
            reranked_hit = SearchHit(hit.chunk, final_score, hit.retrieval_type)
            reranked.append((
                reranked_hit,
                RerankResult(
                    chunk_id=hit.chunk.chunk_id,
                    source=hit.chunk.source,
                    original_score=hit.score,
                    rerank_score=round(rerank_score, 4),
                    final_score=final_score,
                    reason=f"matched_terms={len(overlap)}",
                ),
            ))

        reranked.sort(key=lambda item: (-item[0].score, item[0].chunk.source, item[0].chunk.chunk_id))
        selected = reranked[:top_k]
        return [item[0] for item in selected], [item[1] for item in selected]
