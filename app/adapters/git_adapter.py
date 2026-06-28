"""Git platform adapter interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from time import perf_counter

from app.adapters.base import AdapterResult
from app.adapters.mock_api_client import MockAPIClient
from app.mock.services import GIT_FILE, GIT_SOURCE

MOCK_GIT_API_SOURCE = "mock_api:/mock/git/commits"


class GitAdapter(ABC):
    """Adapter boundary for commit search data sources."""

    @abstractmethod
    def search_commits(self, query: str, context: str = "") -> AdapterResult:
        """Search commit metadata for troubleshooting evidence."""


class LocalGitAdapter(GitAdapter):
    """Local mock Git adapter backed by the in-process mock API."""

    adapter_name = "mock_api_git_adapter"

    def __init__(
        self,
        git_file: Path = GIT_FILE,
        source: str = MOCK_GIT_API_SOURCE,
        client: MockAPIClient | None = None,
    ) -> None:
        self.git_file = git_file
        self.source = source
        self.client = client or MockAPIClient()

    def search_commits(self, query: str, context: str = "") -> AdapterResult:
        started_at = perf_counter()
        if not self.git_file.exists():
            return AdapterResult(
                adapter_name=self.adapter_name,
                status="failed",
                data="",
                source=self.source,
                confidence=0.0,
                error="file_not_found",
                latency_ms=(perf_counter() - started_at) * 1000,
            )

        payload = self.client.get("/mock/git/commits", {"query": query, "context": context})
        latency_ms = (perf_counter() - started_at) * 1000

        return AdapterResult(
            adapter_name=self.adapter_name,
            status=payload.get("status", "failed"),
            data=payload.get("data", ""),
            source=self.source,
            confidence=payload.get("confidence", 0.0),
            error=payload.get("error"),
            latency_ms=payload.get("latency_ms", latency_ms),
        )
