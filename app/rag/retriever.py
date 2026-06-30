"""
Production-style local RAG retriever.

职责边界：
- 只读取 data/docs 下的本地 Markdown
- 支持 Markdown ingestion、chunk metadata、vector/keyword/hybrid retrieval
- 不生成最终答案，不调用 LLM，不访问外部服务
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import time

from app.rag.ingestion import DOCS_SOURCE, MarkdownIngestionPipeline, RagChunk
from app.rag.vector_store import LocalVectorStore, RetrievalHit, keyword_score, metadata_matches

DOCS_DIR = Path(__file__).resolve().parents[2] / DOCS_SOURCE
DEFAULT_SCORE_THRESHOLD = 0.12


class LocalKnowledgeRetriever:
    """基于本地 Markdown 文档的确定性 RAG 检索器。"""

    def __init__(self, docs_dir: Path | None = None):
        self.docs_dir = docs_dir or DOCS_DIR
        self._chunks: list[RagChunk] | None = None
        self._vector_store: LocalVectorStore | None = None

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        score_threshold: float = DEFAULT_SCORE_THRESHOLD,
        metadata_filter: dict[str, Any] | None = None,
        retrieval_type: str = "hybrid",
    ) -> dict[str, Any]:
        start = time.perf_counter()
        markdown_files = self._markdown_files()
        if not markdown_files:
            return self._empty_result(
                query=query,
                top_k=top_k,
                score_threshold=score_threshold,
                retrieval_type=retrieval_type,
                start=start,
                error="knowledge_base_not_found",
            )

        chunks = self._load_chunks(markdown_files)
        if not chunks:
            return self._empty_result(
                query=query,
                top_k=top_k,
                score_threshold=score_threshold,
                retrieval_type=retrieval_type,
                start=start,
                error="knowledge_base_empty",
            )

        fallback_used = False
        vector_available = self._vector_store is not None
        try:
            if retrieval_type == "vector":
                hits = self._vector_hits(query, top_k, score_threshold, metadata_filter)
            elif retrieval_type == "keyword":
                hits = self._keyword_hits(query, top_k, score_threshold, metadata_filter)
            else:
                vector_hits = self._vector_hits(query, top_k * 2, score_threshold, metadata_filter)
                keyword_hits = self._keyword_hits(query, top_k * 2, score_threshold, metadata_filter)
                hits = self._merge_hits(vector_hits, keyword_hits, top_k)
        except Exception:
            fallback_used = True
            vector_available = False
            hits = self._keyword_hits(query, top_k, score_threshold, metadata_filter)

        if retrieval_type in {"vector", "hybrid"} and not vector_available:
            fallback_used = True

        documents = [hit.to_document() for hit in hits[:top_k]]
        grounding_status = self._grounding_status(documents, score_threshold)
        result = {
            "query": query,
            "documents": documents,
            "retrieval_top_k": top_k,
            "score_threshold": score_threshold,
            "retrieved_count": len(documents),
            "grounding_status": grounding_status,
            "retrieval_latency_ms": int((time.perf_counter() - start) * 1000),
            "retrieval_type": "keyword" if fallback_used and retrieval_type != "keyword" else retrieval_type,
            "fallback_used": fallback_used,
            "vector_available": vector_available,
        }

        if not documents:
            result["error"] = "no_relevant_documents"
        elif grounding_status == "insufficient_evidence":
            result["error"] = "insufficient_evidence"
        return result

    def ingest(self) -> list[RagChunk]:
        return self._load_chunks(self._markdown_files())

    def _markdown_files(self) -> list[Path]:
        if not self.docs_dir.exists() or not self.docs_dir.is_dir():
            return []
        return sorted(self.docs_dir.glob("*.md"))

    def _load_chunks(self, markdown_files: list[Path]) -> list[RagChunk]:
        if self._chunks is not None:
            return self._chunks
        if not markdown_files:
            self._chunks = []
            self._vector_store = None
            return []
        pipeline = MarkdownIngestionPipeline(self.docs_dir)
        self._chunks = pipeline.ingest()
        self._vector_store = LocalVectorStore(self._chunks)
        return self._chunks

    def _vector_hits(
        self,
        query: str,
        top_k: int,
        score_threshold: float,
        metadata_filter: dict[str, Any] | None,
    ) -> list[RetrievalHit]:
        if self._vector_store is None:
            return []
        return self._vector_store.search(query, top_k, score_threshold, metadata_filter)

    def _keyword_hits(
        self,
        query: str,
        top_k: int,
        score_threshold: float,
        metadata_filter: dict[str, Any] | None,
    ) -> list[RetrievalHit]:
        chunks = self._chunks or []
        hits = [
            RetrievalHit(chunk=chunk, score=score, retrieval_type="keyword")
            for chunk in chunks
            if metadata_matches(chunk, metadata_filter)
            for score in [keyword_score(query, chunk.content)]
            if score >= score_threshold
        ]
        hits.sort(key=lambda hit: (-hit.score, hit.chunk.chunk_id))
        return hits[:top_k]

    def _merge_hits(
        self,
        vector_hits: list[RetrievalHit],
        keyword_hits: list[RetrievalHit],
        top_k: int,
    ) -> list[RetrievalHit]:
        merged: dict[str, RetrievalHit] = {}
        for hit in vector_hits + keyword_hits:
            existing = merged.get(hit.chunk.chunk_id)
            if existing is None:
                merged[hit.chunk.chunk_id] = hit
                continue
            combined_score = min(1.0, max(existing.score, hit.score) + min(existing.score, hit.score) * 0.15)
            retrieval_type = "hybrid" if existing.retrieval_type != hit.retrieval_type else existing.retrieval_type
            merged[hit.chunk.chunk_id] = RetrievalHit(hit.chunk, combined_score, retrieval_type)

        hits = list(merged.values())
        hits.sort(key=lambda hit: (-hit.score, hit.chunk.chunk_id))
        return hits[:top_k]

    def _grounding_status(self, documents: list[dict[str, Any]], score_threshold: float) -> str:
        if not documents:
            return "insufficient_evidence"
        top_score = max((float(doc.get("score", 0.0)) for doc in documents), default=0.0)
        if top_score < score_threshold:
            return "insufficient_evidence"
        return "grounded"

    def _empty_result(
        self,
        query: str,
        top_k: int,
        score_threshold: float,
        retrieval_type: str,
        start: float,
        error: str,
    ) -> dict[str, Any]:
        return {
            "query": query,
            "documents": [],
            "error": error,
            "retrieval_top_k": top_k,
            "score_threshold": score_threshold,
            "retrieved_count": 0,
            "grounding_status": "insufficient_evidence",
            "retrieval_latency_ms": int((time.perf_counter() - start) * 1000),
            "retrieval_type": retrieval_type,
            "fallback_used": False,
            "vector_available": False,
        }
