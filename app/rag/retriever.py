"""
轻量本地知识库检索器。

职责边界：
- 只读取 data/docs 下的本地 Markdown
- 只做确定性的关键词检索
- 不生成最终答案，不调用 LLM，不访问外部服务
"""

from __future__ import annotations

import re
import string
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DOCS_SOURCE = "data/docs"
DOCS_DIR = Path(__file__).resolve().parents[2] / DOCS_SOURCE

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
class DocumentChunk:
    doc_id: str
    source: str
    content: str


class LocalKnowledgeRetriever:
    """基于本地 Markdown 文档的确定性关键词检索器。"""

    def __init__(self, docs_dir: Path | None = None):
        self.docs_dir = docs_dir or DOCS_DIR

    def retrieve(self, query: str, top_k: int = 3) -> dict[str, Any]:
        markdown_files = self._markdown_files()
        if not markdown_files:
            return {
                "query": query,
                "documents": [],
                "error": "knowledge_base_not_found",
            }

        chunks = self._load_chunks(markdown_files)
        scored = [
            (self._score(query, chunk.content), index, chunk)
            for index, chunk in enumerate(chunks)
        ]
        matched = [
            (score, index, chunk)
            for score, index, chunk in scored
            if score > 0
        ]
        if not matched:
            return {
                "query": query,
                "documents": [],
                "error": "no_relevant_documents",
            }

        matched.sort(key=lambda item: (-item[0], item[1]))
        documents = [
            {
                "doc_id": chunk.doc_id,
                "source": chunk.source,
                "content": chunk.content,
                "score": round(min(score, 1.0), 2),
            }
            for score, _, chunk in matched[:top_k]
        ]
        return {"query": query, "documents": documents}

    def _markdown_files(self) -> list[Path]:
        if not self.docs_dir.exists() or not self.docs_dir.is_dir():
            return []
        return sorted(self.docs_dir.glob("*.md"))

    def _load_chunks(self, markdown_files: list[Path]) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        for path in markdown_files:
            source = f"{DOCS_SOURCE}/{path.name}"
            paragraphs = self._split_markdown(path.read_text(encoding="utf-8"))
            for index, paragraph in enumerate(paragraphs, start=1):
                chunks.append(
                    DocumentChunk(
                        doc_id=f"{path.name}#chunk-{index}",
                        source=source,
                        content=paragraph,
                    )
                )
        return chunks

    def _split_markdown(self, text: str) -> list[str]:
        blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
        chunks: list[str] = []
        for block in blocks:
            if len(block) <= 500:
                chunks.append(block)
                continue
            chunks.extend(block[i:i + 500].strip() for i in range(0, len(block), 500))
        return chunks

    def _score(self, query: str, content: str) -> float:
        query_normalized = self._normalize(query)
        content_normalized = self._normalize(content)
        query_terms = self._terms(query)

        score = 0.0
        for term in query_terms:
            hits = content_normalized.count(term)
            if hits:
                score += 0.2 * min(hits, 3)

        if query_normalized and query_normalized in content_normalized:
            score += 0.35

        phrase_hits = self._phrase_hits(query, content)
        score += 0.15 * phrase_hits
        return score

    def _terms(self, text: str) -> list[str]:
        normalized = self._normalize(text)
        raw_terms = [term for term in normalized.split(" ") if term]
        terms: list[str] = []
        for term in raw_terms:
            if term in _STOP_WORDS:
                continue
            if len(term) == 1 and not term.isdigit():
                continue
            terms.append(term)
            terms.extend(self._chinese_ngrams(term))
        terms.extend(self._chinese_ngrams(text))
        return sorted(set(terms), key=terms.index)

    def _normalize(self, text: str) -> str:
        lowered = text.lower()
        separators = string.punctuation + _CHINESE_PUNCTUATION + "\n\t\r"
        translation = str.maketrans({char: " " for char in separators})
        return " ".join(lowered.translate(translation).split())

    def _phrase_hits(self, query: str, content: str) -> int:
        phrases = re.findall(r"[\u4e00-\u9fff]{2,}|[a-zA-Z_][a-zA-Z0-9_=-]*", query)
        content_lower = content.lower()
        return sum(1 for phrase in phrases if phrase.lower() in content_lower)

    def _chinese_ngrams(self, text: str) -> list[str]:
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
