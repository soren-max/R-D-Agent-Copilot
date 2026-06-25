"""Shared adapter result contract.

Adapters isolate local mock data sources from future real system APIs. They do
not participate in Agent reasoning, tool selection, trace writing, or final
answer generation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias


AdapterData: TypeAlias = dict | list | str
AdapterStatus: TypeAlias = Literal["success", "failed"]


@dataclass(frozen=True)
class AdapterResult:
    """Unified result returned by all system API adapters."""

    adapter_name: str
    status: AdapterStatus
    data: AdapterData
    source: str
    confidence: float
    error: str | None = None
    latency_ms: float = 0.0

    def __post_init__(self) -> None:
        if self.status not in {"success", "failed"}:
            raise ValueError("status must be 'success' or 'failed'")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if self.latency_ms < 0:
            raise ValueError("latency_ms must be greater than or equal to 0")
