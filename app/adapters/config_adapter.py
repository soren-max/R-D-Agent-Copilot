"""Config center adapter interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from time import perf_counter

from app.adapters.base import AdapterResult
from app.adapters.mock_api_client import MockAPIClient
from app.mock.services import CONFIG_SOURCE, DEV_CONFIG_FILE, DEV_CONFIG_SOURCE, PROD_CONFIG_FILE, PROD_CONFIG_SOURCE

MOCK_CONFIG_API_SOURCE = "mock_api:/mock/configs"


class ConfigAdapter(ABC):
    """Adapter boundary for config comparison data sources."""

    @abstractmethod
    def compare_configs(self, query: str, context: str = "") -> AdapterResult:
        """Compare configuration data for troubleshooting evidence."""


class LocalConfigAdapter(ConfigAdapter):
    """Local mock config adapter backed by the in-process mock API."""

    adapter_name = "mock_api_config_adapter"

    def __init__(
        self,
        dev_config_file: Path = DEV_CONFIG_FILE,
        prod_config_file: Path = PROD_CONFIG_FILE,
        source: str = MOCK_CONFIG_API_SOURCE,
        client: MockAPIClient | None = None,
    ) -> None:
        self.dev_config_file = dev_config_file
        self.prod_config_file = prod_config_file
        self.source = source
        self.client = client or MockAPIClient()

    def compare_configs(self, query: str, context: str = "") -> AdapterResult:
        started_at = perf_counter()
        if not self.dev_config_file.exists() or not self.prod_config_file.exists():
            return AdapterResult(
                adapter_name=self.adapter_name,
                status="failed",
                data="",
                source=self.source,
                confidence=0.0,
                error="file_not_found",
                latency_ms=(perf_counter() - started_at) * 1000,
            )

        payload = self.client.get("/mock/configs", {"query": query, "context": context})
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
