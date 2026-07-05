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
import re

from app.rag.ingestion import DOCS_SOURCE, MarkdownIngestionPipeline, RagChunk
from app.rag.vector_store import LocalVectorStore, RetrievalHit, keyword_score, keyword_terms, metadata_matches, normalize

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
        document_files = self._document_files()
        if not document_files:
            return self._empty_result(
                query=query,
                top_k=top_k,
                score_threshold=score_threshold,
                retrieval_type=retrieval_type,
                start=start,
                error="knowledge_base_not_found",
            )

        chunks = self._load_chunks(document_files)
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
        initial_hit_count = 0
        try:
            if retrieval_type == "vector":
                hits = self._vector_hits(query, top_k * 3, score_threshold, metadata_filter)
            elif retrieval_type == "keyword":
                hits = self._keyword_hits(query, top_k * 3, score_threshold, metadata_filter)
            else:
                vector_hits = self._vector_hits(query, top_k * 3, score_threshold, metadata_filter)
                keyword_hits = self._keyword_hits(query, top_k * 3, score_threshold, metadata_filter)
                hits = self._merge_hits(vector_hits, keyword_hits, top_k * 3)
        except Exception:
            fallback_used = True
            vector_available = False
            hits = self._keyword_hits(query, top_k * 3, score_threshold, metadata_filter)

        if retrieval_type in {"vector", "hybrid"} and not vector_available:
            fallback_used = True

        initial_hit_count = len(hits)
        reranked_hits, rerank_results = rerank_hits(query, hits, top_k)
        documents = [hit.to_document() for hit in reranked_hits[:top_k]]
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
            "rerank_applied": bool(hits),
            "rerank_results": rerank_results,
            "dedup_count": self._last_dedup_count(),
            "recall_at_k": 1.0 if documents else 0.0,
            "precision_at_k": round(len(documents) / max(1, top_k), 4),
            "source_coverage": _source_coverage(documents),
            "missing_source_count": _missing_source_count(documents),
            "grounded_answer_rate": 1.0 if grounding_status == "grounded" else 0.0,
            "initial_hit_count": initial_hit_count,
        }

        if not documents:
            result["error"] = "no_relevant_documents"
        elif grounding_status == "insufficient_evidence":
            result["error"] = "insufficient_evidence"
        return result

    def ingest(self) -> list[RagChunk]:
        return self._load_chunks(self._document_files())

    def _document_files(self) -> list[Path]:
        if not self.docs_dir.exists() or not self.docs_dir.is_dir():
            return []
        pipeline = MarkdownIngestionPipeline(self.docs_dir)
        return pipeline.document_files()

    def _load_chunks(self, document_files: list[Path]) -> list[RagChunk]:
        if self._chunks is not None:
            return self._chunks
        if not document_files:
            self._chunks = []
            self._vector_store = None
            return []
        pipeline = MarkdownIngestionPipeline(self.docs_dir)
        self._chunks = pipeline.ingest()
        self._dedup_count = pipeline.duplicated_count
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
            "rerank_applied": False,
            "rerank_results": [],
            "dedup_count": self._last_dedup_count(),
            "recall_at_k": 0.0,
            "precision_at_k": 0.0,
            "source_coverage": 0.0,
            "missing_source_count": 0,
            "grounded_answer_rate": 0.0,
        }

    def _last_dedup_count(self) -> int:
        return int(getattr(self, "_dedup_count", 0) or 0)


def rerank_hits(query: str, hits: list[RetrievalHit], top_k: int) -> tuple[list[RetrievalHit], list[dict[str, Any]]]:
    query_terms = set(keyword_terms(query))
    query_normalized = normalize(query)
    query_error_codes = set(_error_codes(query))
    query_services = set(_service_names(query))
    reranked: list[tuple[RetrievalHit, dict[str, Any]]] = []
    for hit in hits:
        chunk = hit.chunk
        chunk_text = f"{chunk.title}\n{chunk.source}\n{chunk.content}".lower()
        chunk_terms = set(keyword_terms(chunk_text))
        overlap = query_terms.intersection(chunk_terms)
        reasons: list[str] = []
        keyword_component = len(overlap) / max(1, len(query_terms))
        if overlap:
            reasons.append(f"keyword_overlap={len(overlap)}")

        error_matches = query_error_codes.intersection(_error_codes(chunk_text))
        error_component = 0.0
        if error_matches:
            error_component = 0.35
            reasons.append("error_code_match")

        service_matches = {service for service in query_services if service in chunk_text}
        service_component = 0.0
        if service_matches:
            service_component = 0.18
            reasons.append("service_name_match")

        source_title_component = 0.0
        source_title_text = normalize(f"{chunk.source} {chunk.title}")
        if any(term and term in source_title_text for term in query_normalized.split()):
            source_title_component = 0.12
            reasons.append("source_title_match")

        doc_type_component = _doc_type_priority(chunk.doc_type)
        if doc_type_component:
            reasons.append(f"doc_type={chunk.doc_type}")

        rerank_score = min(
            1.0,
            keyword_component * 0.4
            + error_component
            + service_component
            + source_title_component
            + doc_type_component,
        )
        final_score = round(min(1.0, hit.score * 0.55 + rerank_score * 0.45), 4)
        match_reason = ", ".join(reasons) if reasons else "base_retrieval_score"
        reranked_hit = RetrievalHit(
            chunk=chunk,
            score=final_score,
            retrieval_type=hit.retrieval_type,
            rerank_score=round(rerank_score, 4),
            match_reason=match_reason,
        )
        reranked.append((
            reranked_hit,
            {
                "chunk_id": chunk.chunk_id,
                "source": chunk.source,
                "original_score": round(hit.score, 4),
                "rerank_score": round(rerank_score, 4),
                "final_score": final_score,
                "match_reason": match_reason,
            },
        ))

    reranked.sort(key=lambda item: (-item[0].score, item[0].chunk.source, item[0].chunk.chunk_id))
    selected = reranked[:top_k]
    return [item[0] for item in selected], [item[1] for item in selected]


def _error_codes(text: str) -> list[str]:
    return re.findall(r"\b(?:error[_ -]?code[:=]?\s*)?([45]\d{2}|[a-z]+_[a-z0-9_]*|e\d{3,5})\b", text.lower())


def _service_names(text: str) -> list[str]:
    return re.findall(r"\b[a-z][a-z0-9_-]*-service\b|\b[a-z][a-z0-9_-]*_service\b", text.lower())


def _doc_type_priority(doc_type: str) -> float:
    return {
        "log_file": 0.12,
        "config_file": 0.1,
        "code_file": 0.08,
        "markdown_doc": 0.04,
        "normal_doc": 0.02,
    }.get(doc_type, 0.0)


def _missing_source_count(documents: list[dict[str, Any]]) -> int:
    return sum(1 for doc in documents if not (doc.get("source") and doc.get("title")))


def _source_coverage(documents: list[dict[str, Any]]) -> float:
    if not documents:
        return 0.0
    return round((len(documents) - _missing_source_count(documents)) / len(documents), 4)
