"""Safe runtime configuration checks for deployment readiness."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import get_llm_settings
from app.persistence.database import get_database_url
from apps.api.app.rag.loader import KB_DIR, load_markdown_documents
from apps.api.app.rag.embedding_provider import get_embedding_settings
from apps.api.app.rag.rerank_provider import get_rerank_settings

APP_VERSION = "0.8.0"
ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DOCS_DIR = ROOT_DIR / "data" / "docs"


@dataclass(frozen=True)
class CheckItem:
    name: str
    status: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "status": self.status, "detail": self.detail}


def build_config_check() -> dict[str, Any]:
    """Return a deployment-oriented config summary without exposing secrets."""

    llm = get_llm_settings()
    embedding = get_embedding_settings()
    rerank = get_rerank_settings()
    checks = [
        _database_check(),
        _llm_check(llm),
        _kb_check(),
        _provider_check("rag_embedding_provider", embedding.provider, embedding.api_key_configured),
        _provider_check("rag_rerank_provider", rerank.provider, rerank.api_key_configured),
    ]
    status = "ok" if all(item.status in {"ok", "disabled"} for item in checks) else "degraded"
    return {
        "version": APP_VERSION,
        "status": status,
        "checks": [item.to_dict() for item in checks],
        "llm": {
            "enabled": llm.enabled,
            "provider": llm.provider,
            "model": llm.model,
            "base_url_configured": bool(llm.base_url),
            "api_key_configured": bool(llm.api_key),
            "timeout_seconds": llm.timeout_seconds,
        },
        "rag": {
            "kb_dir": str(KB_DIR.relative_to(ROOT_DIR)) if KB_DIR.is_relative_to(ROOT_DIR) else str(KB_DIR),
            "kb_documents": _count_api_kb_documents(),
            "data_docs_dir": str(DATA_DOCS_DIR.relative_to(ROOT_DIR)),
            "data_docs_documents": len(list(DATA_DOCS_DIR.glob("*.md"))) if DATA_DOCS_DIR.exists() else 0,
            "embedding_provider": embedding.provider,
            "embedding_model": embedding.model,
            "embedding_api_key_configured": embedding.api_key_configured,
            "external_calls_enabled": embedding.external_calls_enabled or rerank.external_calls_enabled,
            "rerank_provider": rerank.provider,
            "rerank_model": rerank.model,
            "rerank_api_key_configured": rerank.api_key_configured,
        },
    }


def _database_check() -> CheckItem:
    database_url = get_database_url()
    status = "ok" if database_url.startswith("sqlite:///") else "error"
    detail = "SQLite configured" if status == "ok" else "Only SQLite is supported in the local demo"
    return CheckItem("database", status, detail)


def _llm_check(llm: Any) -> CheckItem:
    if not llm.enabled:
        return CheckItem("llm", "disabled", "LLM is disabled; fallback answer path is active")
    if not llm.api_key:
        return CheckItem("llm", "error", "LLM is enabled but API key is not configured")
    return CheckItem("llm", "ok", f"{llm.provider}/{llm.model} configured")


def _kb_check() -> CheckItem:
    count = _count_api_kb_documents()
    if count == 0:
        return CheckItem("kb", "error", "No local Markdown knowledge documents found")
    return CheckItem("kb", "ok", f"{count} local Markdown knowledge documents loaded")


def _provider_check(name: str, provider: str, api_key_configured: bool) -> CheckItem:
    if provider == "local":
        return CheckItem(name, "ok", "local deterministic fallback provider active")
    if api_key_configured:
        return CheckItem(name, "ok", f"{provider} configured")
    return CheckItem(name, "disabled", f"{provider} requested without API key; local fallback will be used")


def _count_api_kb_documents() -> int:
    try:
        return len(load_markdown_documents(KB_DIR))
    except Exception:
        return 0
