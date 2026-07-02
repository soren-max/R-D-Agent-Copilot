"""Keyword search over local knowledge chunks."""

from __future__ import annotations

from dataclasses import dataclass

from apps.api.app.rag.chunker import KnowledgeChunk, extract_keywords


@dataclass(frozen=True)
class SearchHit:
    chunk: KnowledgeChunk
    score: float


class KeywordSearchIndex:
    def __init__(self, chunks: list[KnowledgeChunk]):
        self.chunks = chunks

    def search(self, query: str, top_k: int = 3) -> list[SearchHit]:
        query_keywords = extract_keywords(query)
        if not query_keywords:
            return []

        hits: list[SearchHit] = []
        query_set = set(query_keywords)
        for chunk in self.chunks:
            keyword_overlap = query_set.intersection(chunk.keywords)
            content_hits = {
                keyword for keyword in query_keywords
                if keyword in chunk.content.lower() or keyword in chunk.title.lower()
            }
            matched = keyword_overlap.union(content_hits)
            if not matched:
                continue
            score = min(1.0, len(matched) / max(1, len(query_set)) + 0.08 * len(keyword_overlap))
            hits.append(SearchHit(chunk=chunk, score=round(score, 4)))

        hits.sort(key=lambda hit: (-hit.score, hit.chunk.source, hit.chunk.chunk_id))
        return hits[:top_k]
