"""Git platform adapter interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from time import perf_counter

from app.adapters.base import AdapterResult


class GitAdapter(ABC):
    """Adapter boundary for commit search data sources."""

    @abstractmethod
    def search_commits(self, query: str, context: str = "") -> AdapterResult:
        """Search commit metadata for troubleshooting evidence."""


class LocalGitAdapter(GitAdapter):
    """Local mock Git adapter skeleton.

    Future PRs may wire this adapter to ``data/git/commits.json`` from tools.
    This skeleton intentionally avoids external API calls.
    """

    adapter_name = "local_git_adapter"
    source = "data/git/commits.json"

    def search_commits(self, query: str, context: str = "") -> AdapterResult:
        started_at = perf_counter()
        data = {
            "query": query,
            "context": context,
            "message": "local git adapter skeleton; tool integration pending",
        }
        latency_ms = (perf_counter() - started_at) * 1000

        return AdapterResult(
            adapter_name=self.adapter_name,
            status="success",
            data=data,
            source=self.source,
            confidence=0.0,
            error=None,
            latency_ms=latency_ms,
        )
