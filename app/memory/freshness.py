"""Freshness classification for incident memories."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.memory.incident_memory import IncidentMemory


@dataclass
class FreshnessResult:
    freshness_status: str
    reason: str = ""


def evaluate_freshness(memory: IncidentMemory, ttl_days: int = 30) -> FreshnessResult:
    if not memory.source_run_id or not memory.created_at or not memory.evidence_refs:
        return FreshnessResult("weak", "missing_source_or_evidence")

    try:
        created_at = datetime.fromisoformat(memory.created_at)
    except ValueError:
        return FreshnessResult("weak", "invalid_created_at")
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    age_days = (datetime.now(timezone.utc) - created_at).days
    if age_days > ttl_days:
        return FreshnessResult("stale", f"older_than_{ttl_days}_days")
    return FreshnessResult("fresh", "within_ttl")
