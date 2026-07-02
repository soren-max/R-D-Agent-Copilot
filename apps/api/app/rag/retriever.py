"""v0.3.0 keyword-only retriever."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from apps.api.app.rag.chunker import chunk_documents
from apps.api.app.rag.evidence import build_evidence
from apps.api.app.rag.grounding import evaluate_grounding
from apps.api.app.rag.keyword_search import KeywordSearchIndex, SearchHit
from apps.api.app.rag.loader import KB_DIR, load_markdown_documents
from apps.api.app.rag.query_rewrite import rewrite_query


class KeywordRetriever:
    def __init__(self, kb_dir: Path | None = None):
        self.kb_dir = kb_dir or KB_DIR
        self._hits_cache: dict[tuple[str, int], list[SearchHit]] = {}

    def chunks(self):
        return chunk_documents(load_markdown_documents(self.kb_dir))

    def retrieve(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Return relevant chunk dictionaries. No matches returns an empty list."""

        hits = self.search(query, top_k=top_k)
        return [
            {
                **hit.chunk.to_dict(score=hit.score),
                "retrieval_type": "keyword",
            }
            for hit in hits
        ]

    def search(self, query: str, top_k: int = 3) -> list[SearchHit]:
        cache_key = (query, top_k)
        if cache_key not in self._hits_cache:
            index = KeywordSearchIndex(self.chunks())
            rewrite = rewrite_query(query)
            merged: dict[str, SearchHit] = {}
            for rewritten_query in rewrite.all_queries():
                for hit in index.search(rewritten_query, top_k=top_k * 2):
                    existing = merged.get(hit.chunk.chunk_id)
                    if existing is None or hit.score > existing.score:
                        merged[hit.chunk.chunk_id] = hit
            hits = list(merged.values())
            hits.sort(key=lambda hit: (-hit.score, hit.chunk.source, hit.chunk.chunk_id))
            self._hits_cache[cache_key] = hits[:top_k]
        return self._hits_cache[cache_key]

    def retrieve_with_evidence(self, query: str, top_k: int = 3) -> dict[str, Any]:
        rewrite = rewrite_query(query)
        hits = self.search(query, top_k=top_k)
        chunks = self.retrieve(query, top_k=top_k)
        evidence = build_evidence(hits)
        grounding = evaluate_grounding(evidence)
        return {
            "query": query,
            "rewritten_queries": rewrite.all_queries(),
            "query_expansions": rewrite.expansions,
            "retrieved_chunks": chunks,
            "evidence": [item.to_dict() for item in evidence],
            "grounding_status": grounding.grounding_status,
            "no_evidence_reason": grounding.no_evidence_reason,
            "retrieved_count": len(chunks),
            "retrieval_top_k": top_k,
            "retrieval_type": "keyword",
        }
