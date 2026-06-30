"""
Deterministic local vector store for RAG retrieval.

This is intentionally dependency-light: vectors are built with token hashing
and searched in memory. It gives the product surface of vector retrieval while
remaining safe for tests and demos without external services or model downloads.
"""

from __future__ import annotations

import math
import re
import string
from collections import Counter
from dataclasses import dataclass
from hashlib import blake2b
from typing import Any

from app.rag.ingestion import RagChunk

VECTOR_DIMENSIONS = 256
_CHINESE_PUNCTUATION = "，。！？；：、“”‘’（）【】《》、"
_STOP_WORDS = {
    "什么",
    "如何",
    "为什么",
    "怎么",
    "一个",
    "一下",
    "the",
    "and",
    "or",
    "is",
}


@dataclass(frozen=True)
class RetrievalHit:
    chunk: RagChunk
    score: float
    retrieval_type: str

    def to_document(self) -> dict[str, Any]:
        metadata = self.chunk.metadata
        return {
            "content": self.chunk.content,
            "source": metadata["source"],
            "title": metadata["title"],
            "section": metadata["section"],
            "score": round(self.score, 4),
            "chunk_id": metadata["chunk_id"],
            "doc_type": metadata["doc_type"],
            "updated_at": metadata["updated_at"],
            "retrieval_type": self.retrieval_type,
        }


class LocalVectorStore:
    """In-memory vector index over ingested chunks."""

    def __init__(self, chunks: list[RagChunk]) -> None:
        self.chunks = chunks
        self._vectors = [embed_text(chunk.content) for chunk in chunks]
        self._token_sets = [set(tokenize(chunk.content)) for chunk in chunks]

    def search(
        self,
        query: str,
        top_k: int = 3,
        score_threshold: float = 0.0,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[RetrievalHit]:
        query_vector = embed_text(query)
        hits: list[RetrievalHit] = []
        query_tokens = set(tokenize(query))
        for chunk, vector, chunk_tokens in zip(self.chunks, self._vectors, self._token_sets, strict=True):
            if not metadata_matches(chunk, metadata_filter):
                continue
            if query_tokens and not query_tokens.intersection(chunk_tokens):
                continue
            score = cosine_similarity(query_vector, vector)
            if score >= score_threshold:
                hits.append(RetrievalHit(chunk=chunk, score=score, retrieval_type="vector"))

        hits.sort(key=lambda hit: (-hit.score, hit.chunk.chunk_id))
        return hits[:top_k]


def embed_text(text: str) -> list[float]:
    tokens = tokenize(text)
    vector = [0.0] * VECTOR_DIMENSIONS
    if not tokens:
        return vector

    counts = Counter(tokens)
    for token, count in counts.items():
        digest = blake2b(token.encode("utf-8"), digest_size=4).digest()
        index = int.from_bytes(digest, "big") % VECTOR_DIMENSIONS
        vector[index] += 1.0 + math.log(count)

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return max(0.0, min(1.0, sum(a * b for a, b in zip(left, right, strict=True))))


def metadata_matches(chunk: RagChunk, metadata_filter: dict[str, Any] | None) -> bool:
    if not metadata_filter:
        return True
    metadata = chunk.metadata
    return all(metadata.get(key) == value for key, value in metadata_filter.items())


def keyword_score(query: str, content: str) -> float:
    query_normalized = normalize(query)
    content_normalized = normalize(content)
    terms = keyword_terms(query)

    score = 0.0
    for term in terms:
        hits = content_normalized.count(term)
        if hits:
            score += 0.12 * min(hits, 4)

    if query_normalized and query_normalized in content_normalized:
        score += 0.35

    phrase_hits = phrase_hits_count(query, content)
    score += 0.12 * phrase_hits
    return min(score, 1.0)


def keyword_terms(text: str) -> list[str]:
    normalized = normalize(text)
    raw_terms = [term for term in normalized.split(" ") if term]
    terms: list[str] = []
    for term in raw_terms:
        if term in _STOP_WORDS:
            continue
        if len(term) == 1 and not term.isdigit():
            continue
        terms.append(term)
        terms.extend(chinese_ngrams(term))
    terms.extend(chinese_ngrams(text))
    return sorted(set(terms), key=terms.index)


def tokenize(text: str) -> list[str]:
    base_terms = keyword_terms(text)
    ascii_terms = re.findall(r"[a-zA-Z_][a-zA-Z0-9_./#=-]*|\d+", text.lower())
    chinese_terms = chinese_ngrams(text)
    return sorted(set(base_terms + ascii_terms + chinese_terms), key=(base_terms + ascii_terms + chinese_terms).index)


def normalize(text: str) -> str:
    lowered = text.lower()
    separators = string.punctuation + _CHINESE_PUNCTUATION + "\n\t\r"
    translation = str.maketrans({char: " " for char in separators})
    return " ".join(lowered.translate(translation).split())


def phrase_hits_count(query: str, content: str) -> int:
    phrases = re.findall(r"[\u4e00-\u9fff]{2,}|[a-zA-Z_][a-zA-Z0-9_=-]*", query)
    content_lower = content.lower()
    return sum(1 for phrase in phrases if phrase.lower() in content_lower)


def chinese_ngrams(text: str) -> list[str]:
    grams: list[str] = []
    for sequence in re.findall(r"[\u4e00-\u9fff]{2,}", text):
        for prefix in ["什么是", "为什么", "如何", "怎么", "什么"]:
            if sequence.startswith(prefix):
                sequence = sequence[len(prefix):]
                break
        if len(sequence) < 2:
            continue
        max_size = min(len(sequence), 6)
        for size in range(2, max_size + 1):
            for start in range(0, len(sequence) - size + 1):
                grams.append(sequence[start:start + size])
    return grams
