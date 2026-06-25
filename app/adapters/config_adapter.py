"""Config center adapter interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from time import perf_counter

from app.adapters.base import AdapterResult


class ConfigAdapter(ABC):
    """Adapter boundary for config comparison data sources."""

    @abstractmethod
    def compare_configs(self, query: str, context: str = "") -> AdapterResult:
        """Compare configuration data for troubleshooting evidence."""


class LocalConfigAdapter(ConfigAdapter):
    """Local mock config adapter skeleton.

    Future PRs may wire this adapter to ``data/configs/dev.json`` and
    ``data/configs/prod.json`` from tools. This skeleton intentionally avoids
    external API calls.
    """

    adapter_name = "local_config_adapter"
    source = "data/configs/dev.json,data/configs/prod.json"

    def compare_configs(self, query: str, context: str = "") -> AdapterResult:
        started_at = perf_counter()
        data = {
            "query": query,
            "context": context,
            "message": "local config adapter skeleton; tool integration pending",
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
