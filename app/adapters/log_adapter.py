"""Log system adapter interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from time import perf_counter

from app.adapters.base import AdapterResult


class LogAdapter(ABC):
    """Adapter boundary for log search data sources."""

    @abstractmethod
    def search_logs(self, query: str, context: str = "") -> AdapterResult:
        """Search logs for troubleshooting evidence."""


class LocalLogAdapter(LogAdapter):
    """Local mock log adapter skeleton.

    Future PRs may wire this adapter to ``data/logs/order-service.log`` from
    tools. This skeleton intentionally avoids external API calls.
    """

    adapter_name = "local_log_adapter"
    source = "data/logs/order-service.log"

    def search_logs(self, query: str, context: str = "") -> AdapterResult:
        started_at = perf_counter()
        data = {
            "query": query,
            "context": context,
            "message": "local log adapter skeleton; tool integration pending",
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
