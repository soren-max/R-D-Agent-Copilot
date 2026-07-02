"""Evidence construction from retrieved chunks."""

from __future__ import annotations

from dataclasses import dataclass

from apps.api.app.rag.keyword_search import SearchHit


@dataclass(frozen=True)
class Evidence:
    source: str
    chunk_id: str
    content_excerpt: str
    score: float

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "chunk_id": self.chunk_id,
            "content_excerpt": self.content_excerpt,
            "score": self.score,
        }


def build_evidence(hits: list[SearchHit], excerpt_chars: int = 260) -> list[Evidence]:
    evidence: list[Evidence] = []
    for hit in hits:
        excerpt = " ".join(hit.chunk.content.split())
        if len(excerpt) > excerpt_chars:
            excerpt = f"{excerpt[:excerpt_chars - 3]}..."
        evidence.append(
            Evidence(
                source=hit.chunk.source,
                chunk_id=hit.chunk.chunk_id,
                content_excerpt=excerpt,
                score=hit.score,
            )
        )
    return evidence
