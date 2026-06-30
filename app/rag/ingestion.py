"""
Local Markdown ingestion for the RAG knowledge base.

The ingestion layer is deterministic and local-only:
- reads data/docs/*.md
- chunks on Markdown heading, paragraph, and fenced-code boundaries
- preserves metadata needed by retrieval, trace, and evaluation
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DOCS_SOURCE = "data/docs"
DEFAULT_CHUNK_SIZE = 650
DEFAULT_CHUNK_OVERLAP = 100


@dataclass(frozen=True)
class RagChunk:
    content: str
    source: str
    title: str
    section: str
    chunk_id: str
    doc_type: str
    updated_at: str

    @property
    def metadata(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "title": self.title,
            "section": self.section,
            "chunk_id": self.chunk_id,
            "doc_type": self.doc_type,
            "updated_at": self.updated_at,
        }


class MarkdownIngestionPipeline:
    """Build production-style chunks from local Markdown documents."""

    def __init__(
        self,
        docs_dir: Path,
        docs_source: str = DOCS_SOURCE,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        self.docs_dir = docs_dir
        self.docs_source = docs_source
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def ingest(self) -> list[RagChunk]:
        chunks: list[RagChunk] = []
        for path in self.markdown_files():
            chunks.extend(self._ingest_file(path))
        return chunks

    def markdown_files(self) -> list[Path]:
        if not self.docs_dir.exists() or not self.docs_dir.is_dir():
            return []
        return sorted(self.docs_dir.glob("*.md"))

    def _ingest_file(self, path: Path) -> list[RagChunk]:
        text = path.read_text(encoding="utf-8")
        source = f"{self.docs_source}/{path.name}"
        updated_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
        doc_type = "markdown"
        title = self._first_heading(text) or path.stem
        blocks = self._markdown_blocks(text)

        raw_chunks: list[tuple[str, str]] = []
        active_section = title
        buffer: list[str] = []
        buffer_tokens = 0

        def flush() -> None:
            nonlocal buffer, buffer_tokens
            if not buffer:
                return
            content = "\n\n".join(buffer).strip()
            if content:
                raw_chunks.extend((active_section, chunk) for chunk in self._split_large_block(content))
            buffer = []
            buffer_tokens = 0

        for block in blocks:
            heading = self._heading_text(block)
            if heading:
                flush()
                active_section = heading
                buffer = [block]
                buffer_tokens = self._token_count(block)
                continue

            block_tokens = self._token_count(block)
            if buffer and buffer_tokens + block_tokens > self.chunk_size:
                flush()
            buffer.append(block)
            buffer_tokens += block_tokens

        flush()

        chunks: list[RagChunk] = []
        for index, (section, content) in enumerate(raw_chunks, start=1):
            chunks.append(
                RagChunk(
                    content=content,
                    source=source,
                    title=title,
                    section=section,
                    chunk_id=f"{path.stem}#chunk-{index}",
                    doc_type=doc_type,
                    updated_at=updated_at,
                )
            )
        return chunks

    def _markdown_blocks(self, text: str) -> list[str]:
        blocks: list[str] = []
        current: list[str] = []
        in_code = False

        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("```"):
                current.append(line)
                in_code = not in_code
                if not in_code:
                    blocks.append("\n".join(current).strip())
                    current = []
                continue

            if in_code:
                current.append(line)
                continue

            if re.match(r"^#{1,6}\s+", stripped):
                if current:
                    blocks.append("\n".join(current).strip())
                    current = []
                blocks.append(stripped)
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

    def _split_large_block(self, text: str) -> list[str]:
        tokens = self._tokens(text)
        if len(tokens) <= self.chunk_size:
            return [text]

        chunks: list[str] = []
        step = max(1, self.chunk_size - self.chunk_overlap)
        for start in range(0, len(tokens), step):
            chunk_tokens = tokens[start:start + self.chunk_size]
            if not chunk_tokens:
                continue
            chunks.append(" ".join(chunk_tokens).strip())
            if start + self.chunk_size >= len(tokens):
                break
        return chunks

    def _first_heading(self, text: str) -> str | None:
        for line in text.splitlines():
            heading = self._heading_text(line)
            if heading:
                return heading
        return None

    def _heading_text(self, block: str) -> str | None:
        match = re.match(r"^#{1,6}\s+(.+)$", block.strip())
        return match.group(1).strip() if match else None

    def _token_count(self, text: str) -> int:
        return len(self._tokens(text))

    def _tokens(self, text: str) -> list[str]:
        return re.findall(r"[\u4e00-\u9fff]|[a-zA-Z0-9_./#=-]+", text.lower())
