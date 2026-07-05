"""
Local layered ingestion for the RAG knowledge base.

The ingestion layer is deterministic and local-only:
- reads local knowledge documents from data/docs
- detects document type and applies layered chunking
- cleans noisy text while preserving troubleshooting evidence
- preserves metadata needed by retrieval, trace, and evaluation
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import blake2b
from pathlib import Path
from typing import Any

DOCS_SOURCE = "data/docs"
DEFAULT_CHUNK_SIZE = 650
DEFAULT_CHUNK_OVERLAP = 100
LARGE_CHUNK_SIZE = 650
SMALL_CHUNK_SIZE = 220
SUPPORTED_EXTENSIONS = {
    ".md",
    ".markdown",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".env",
    ".properties",
    ".log",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".java",
    ".go",
    ".rb",
    ".sh",
}


@dataclass(frozen=True)
class RagChunk:
    content: str
    source: str
    title: str
    section: str
    chunk_id: str
    doc_type: str
    updated_at: str
    line_range: tuple[int, int]
    content_hash: str

    @property
    def metadata(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "title": self.title,
            "section": self.section,
            "chunk_id": self.chunk_id,
            "doc_type": self.doc_type,
            "updated_at": self.updated_at,
            "line_range": list(self.line_range),
            "content_hash": self.content_hash,
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
        self.duplicated_count = 0

    def ingest(self) -> list[RagChunk]:
        chunks: list[RagChunk] = []
        for path in self.document_files():
            chunks.extend(self._ingest_file(path))
        chunks, duplicated_count = deduplicate_chunks(chunks)
        self.duplicated_count = duplicated_count
        return chunks

    def markdown_files(self) -> list[Path]:
        return [path for path in self.document_files() if path.suffix.lower() in {".md", ".markdown"}]

    def document_files(self) -> list[Path]:
        if not self.docs_dir.exists() or not self.docs_dir.is_dir():
            return []
        return sorted(
            path for path in self.docs_dir.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        )

    def _ingest_file(self, path: Path) -> list[RagChunk]:
        text = path.read_text(encoding="utf-8")
        source = f"{self.docs_source}/{path.name}"
        updated_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
        doc_type = detect_doc_type(path)
        title = self._first_heading(text) or path.stem
        blocks = self._blocks_for_doc_type(text, doc_type)
        chunk_size = self._chunk_size_for_doc_type(doc_type)

        raw_chunks: list[tuple[str, str, tuple[int, int]]] = []
        if doc_type in {"config_file", "log_file", "code_file"}:
            for block, line_range in blocks:
                raw_chunks.extend(
                    (title, chunk, line_range)
                    for chunk in self._split_large_block(block, chunk_size)
                )
            return self._build_chunks(path, source, title, doc_type, updated_at, raw_chunks)

        active_section = title
        buffer: list[tuple[str, tuple[int, int]]] = []
        buffer_tokens = 0

        def flush() -> None:
            nonlocal buffer, buffer_tokens
            if not buffer:
                return
            content = "\n\n".join(item[0] for item in buffer).strip()
            if content:
                line_range = (buffer[0][1][0], buffer[-1][1][1])
                raw_chunks.extend(
                    (active_section, chunk, line_range)
                    for chunk in self._split_large_block(content, chunk_size)
                )
            buffer = []
            buffer_tokens = 0

        for block, line_range in blocks:
            heading = self._heading_text(block)
            if heading:
                flush()
                active_section = heading
                buffer = [(block, line_range)]
                buffer_tokens = self._token_count(block)
                continue

            block_tokens = self._token_count(block)
            if buffer and buffer_tokens + block_tokens > chunk_size:
                flush()
            buffer.append((block, line_range))
            buffer_tokens += block_tokens

        flush()

        return self._build_chunks(path, source, title, doc_type, updated_at, raw_chunks)

    def _build_chunks(
        self,
        path: Path,
        source: str,
        title: str,
        doc_type: str,
        updated_at: str,
        raw_chunks: list[tuple[str, str, tuple[int, int]]],
    ) -> list[RagChunk]:
        chunks: list[RagChunk] = []
        for index, (section, content, line_range) in enumerate(raw_chunks, start=1):
            cleaned = clean_text(content, doc_type)
            if not cleaned:
                continue
            chunks.append(
                RagChunk(
                    content=cleaned,
                    source=source,
                    title=title,
                    section=section,
                    chunk_id=f"{path.stem}#chunk-{index}",
                    doc_type=doc_type,
                    updated_at=updated_at,
                    line_range=line_range,
                    content_hash=content_hash(cleaned),
                )
            )
        return chunks

    def _blocks_for_doc_type(self, text: str, doc_type: str) -> list[tuple[str, tuple[int, int]]]:
        if doc_type == "markdown_doc":
            return self._markdown_blocks(text)
        if doc_type == "log_file":
            return self._line_window_blocks(text, window_size=8)
        if doc_type == "config_file":
            return self._line_window_blocks(text, window_size=10)
        if doc_type == "code_file":
            return self._code_blocks(text)
        return self._paragraph_blocks(text)

    def _markdown_blocks(self, text: str) -> list[tuple[str, tuple[int, int]]]:
        blocks: list[tuple[str, tuple[int, int]]] = []
        current: list[tuple[int, str]] = []
        in_code = False

        for line_number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("```"):
                current.append((line_number, line))
                in_code = not in_code
                if not in_code:
                    blocks.append(_block_from_lines(current))
                    current = []
                continue

            if in_code:
                current.append((line_number, line))
                continue

            if re.match(r"^#{1,6}\s+", stripped):
                if current:
                    blocks.append(_block_from_lines(current))
                    current = []
                blocks.append((stripped, (line_number, line_number)))
                continue

            if not stripped:
                if current:
                    blocks.append(_block_from_lines(current))
                    current = []
                continue

            current.append((line_number, line))

        if current:
            blocks.append(_block_from_lines(current))

        return [block for block in blocks if block[0]]

    def _paragraph_blocks(self, text: str) -> list[tuple[str, tuple[int, int]]]:
        blocks: list[tuple[str, tuple[int, int]]] = []
        current: list[tuple[int, str]] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                if current:
                    blocks.append(_block_from_lines(current))
                    current = []
                continue
            current.append((line_number, line))
        if current:
            blocks.append(_block_from_lines(current))
        return [block for block in blocks if block[0]]

    def _line_window_blocks(self, text: str, window_size: int) -> list[tuple[str, tuple[int, int]]]:
        lines = [(line_number, line) for line_number, line in enumerate(text.splitlines(), start=1) if line.strip()]
        blocks: list[tuple[str, tuple[int, int]]] = []
        for start in range(0, len(lines), window_size):
            window = lines[start:start + window_size]
            if window:
                blocks.append(_block_from_lines(window))
        return blocks

    def _code_blocks(self, text: str) -> list[tuple[str, tuple[int, int]]]:
        blocks: list[tuple[str, tuple[int, int]]] = []
        current: list[tuple[int, str]] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            starts_symbol = re.match(r"^(def|class|function|func|public|private|protected|export)\b", stripped)
            if starts_symbol and current:
                blocks.append(_block_from_lines(current))
                current = []
            if stripped:
                current.append((line_number, line))
        if current:
            blocks.append(_block_from_lines(current))
        return blocks

    def _split_large_block(self, text: str, chunk_size: int) -> list[str]:
        tokens = self._tokens(text)
        if len(tokens) <= chunk_size:
            return [text]

        chunks: list[str] = []
        overlap = min(self.chunk_overlap, max(0, chunk_size // 3))
        step = max(1, chunk_size - overlap)
        for start in range(0, len(tokens), step):
            chunk_tokens = tokens[start:start + chunk_size]
            if not chunk_tokens:
                continue
            chunks.append(" ".join(chunk_tokens).strip())
            if start + chunk_size >= len(tokens):
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

    def _chunk_size_for_doc_type(self, doc_type: str) -> int:
        if doc_type in {"config_file", "log_file", "code_file"}:
            return min(self.chunk_size, SMALL_CHUNK_SIZE)
        return max(self.chunk_size, LARGE_CHUNK_SIZE)


def detect_doc_type(path: Path) -> str:
    suffix = path.suffix.lower()
    name = path.name.lower()
    if suffix in {".md", ".markdown"}:
        return "markdown_doc"
    if suffix == ".log" or "log" in name:
        return "log_file"
    if suffix in {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env", ".properties"}:
        return "config_file"
    if suffix in {".py", ".js", ".ts", ".tsx", ".java", ".go", ".rb", ".sh"}:
        return "code_file"
    return "normal_doc"


def clean_text(text: str, doc_type: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    cleaned: list[str] = []
    seen_template_lines: set[str] = set()
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if _looks_garbled(stripped):
            continue
        normalized = normalize_text(stripped)
        if _is_template_noise(normalized):
            if normalized in seen_template_lines:
                continue
            seen_template_lines.add(normalized)
        cleaned.append(_clean_line_for_doc_type(stripped, doc_type))
    return "\n".join(line for line in cleaned if line).strip()


def normalize_text(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"\b[0-9a-f]{8,}\b", "<hex>", lowered)
    lowered = re.sub(r"\b\d{4}-\d{2}-\d{2}[t\s]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?z?\b", "<timestamp>", lowered)
    lowered = re.sub(r"\b\d+\b", "<num>", lowered)
    return " ".join(lowered.split())


def content_hash(text: str) -> str:
    return blake2b(normalize_text(text).encode("utf-8"), digest_size=8).hexdigest()


def deduplicate_chunks(chunks: list[RagChunk]) -> tuple[list[RagChunk], int]:
    kept: list[RagChunk] = []
    seen_by_hash: dict[str, RagChunk] = {}
    duplicated_count = 0
    for chunk in chunks:
        existing = seen_by_hash.get(chunk.content_hash)
        if existing is not None and not (_is_critical_evidence(existing) or _is_critical_evidence(chunk)):
            duplicated_count += 1
            continue
        seen_by_hash.setdefault(chunk.content_hash, chunk)
        kept.append(chunk)
    return kept, duplicated_count


def _block_from_lines(lines: list[tuple[int, str]]) -> tuple[str, tuple[int, int]]:
    return "\n".join(line for _, line in lines).strip(), (lines[0][0], lines[-1][0])


def _looks_garbled(text: str) -> bool:
    if "\ufffd" in text:
        return True
    if not text:
        return False
    printable = sum(1 for char in text if char.isprintable())
    return printable / max(1, len(text)) < 0.75


def _is_template_noise(normalized: str) -> bool:
    templates = {
        "copyright <num>",
        "all rights reserved",
        "generated by system",
        "template placeholder",
    }
    return normalized in templates


def _clean_line_for_doc_type(line: str, doc_type: str) -> str:
    if doc_type == "log_file":
        return line[:500]
    if doc_type == "config_file":
        return line
    if doc_type == "code_file":
        return line[:500]
    return line


def _is_critical_evidence(chunk: RagChunk) -> bool:
    text = chunk.content.lower()
    if chunk.doc_type in {"log_file", "config_file", "code_file"}:
        return bool(
            re.search(r"\b(error|exception|traceback|fatal|warn|timeout|[45]\d{2}|e\d{3,5})\b", text)
            or re.search(r"^[a-zA-Z0-9_.-]+\s*[:=]", text, flags=re.MULTILINE)
            or re.search(r"\b(def|class|function|func)\s+[a-zA-Z_][a-zA-Z0-9_]*", text)
        )
    return False
