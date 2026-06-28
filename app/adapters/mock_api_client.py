"""In-process client for local mock platform API semantics."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from app.mock.services import compare_mock_configs, search_mock_commits, search_mock_logs


class MockAPIClient:
    """Dispatches local mock API paths without external network IO."""

    def get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        started_at = perf_counter()
        query = str(params.get("query", ""))
        context = str(params.get("context", ""))
        if path == "/mock/logs":
            data = search_mock_logs(query=query, context=context)
        elif path == "/mock/configs":
            data = compare_mock_configs(query=query, context=context)
        elif path == "/mock/git/commits":
            data = search_mock_commits(query=query, context=context)
        else:
            data = {
                "status": "failed",
                "data": "",
                "source": f"mock_api:{path}",
                "confidence": 0.0,
                "error": "mock_endpoint_not_found",
                "metadata": {},
            }

        if "latency_ms" not in data:
            data["latency_ms"] = (perf_counter() - started_at) * 1000
        return data
