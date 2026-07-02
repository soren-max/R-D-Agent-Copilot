"""Local Markdown knowledge-base loader."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

KB_DIR = Path(__file__).resolve().parents[1] / "kb"


@dataclass(frozen=True)
class MarkdownDocument:
    source: str
    title: str
    content: str


def load_markdown_documents(kb_dir: Path | None = None) -> list[MarkdownDocument]:
    """Load local Markdown files from the v0.3.0 KB directory."""

    root = kb_dir or KB_DIR
    if not root.exists() or not root.is_dir():
        return []

    documents: list[MarkdownDocument] = []
    for path in sorted(root.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        documents.append(
            MarkdownDocument(
                source=f"apps/api/app/kb/{path.name}",
                title=_first_heading(content) or path.stem,
                content=content,
            )
        )
    from apps.api.app.safety.kb_filter import filter_malicious_documents

    allowed, _ = filter_malicious_documents(documents)
    return allowed


def _first_heading(content: str) -> str | None:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return None
