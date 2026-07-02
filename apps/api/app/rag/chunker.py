"""Markdown chunking and keyword extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from apps.api.app.rag.loader import MarkdownDocument


@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    source: str
    title: str
    content: str
    keywords: list[str] = field(default_factory=list)

    def to_dict(self, score: float | None = None) -> dict[str, object]:
        data: dict[str, object] = {
            "chunk_id": self.chunk_id,
            "source": self.source,
            "title": self.title,
            "content": self.content,
            "keywords": self.keywords,
        }
        if score is not None:
            data["score"] = score
        return data


def chunk_documents(documents: list[MarkdownDocument], max_chars: int = 900) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    for document in documents:
        blocks = _blocks(document.content)
        buffer: list[str] = []
        index = 1
        for block in blocks:
            candidate = "\n\n".join(buffer + [block]).strip()
            if buffer and len(candidate) > max_chars:
                chunks.append(_make_chunk(document, index, "\n\n".join(buffer)))
                index += 1
                buffer = [block]
            else:
                buffer.append(block)
        if buffer:
            chunks.append(_make_chunk(document, index, "\n\n".join(buffer)))
    return chunks


def extract_keywords(text: str) -> list[str]:
    """Extract deterministic Chinese/English troubleshooting keywords."""

    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]*|[0-9]{2,5}|[\u4e00-\u9fff]{2,}", text.lower())
    stopwords = {
        "the", "and", "for", "with", "this", "that",
        "如果", "需要", "可以", "建议", "检查", "处理",
    }
    keywords: list[str] = []
    for token in tokens:
        if token in stopwords:
            continue
        if token not in keywords:
            keywords.append(token)
    return keywords[:40]


def _make_chunk(document: MarkdownDocument, index: int, content: str) -> KnowledgeChunk:
    return KnowledgeChunk(
        chunk_id=f"{document.source.rsplit('/', 1)[-1]}#chunk-{index}",
        source=document.source,
        title=document.title,
        content=content.strip(),
        keywords=extract_keywords(f"{document.title}\n{content}"),
    )


def _blocks(content: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            current.append(stripped)
            continue
        if not stripped:
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            continue
        current.append(line)
    if current:
        blocks.append("\n".join(current).strip())
    return [block for block in blocks if block]
