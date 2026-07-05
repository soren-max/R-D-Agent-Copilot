"""Rule-based checkpoint drift checks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.resume.checkpoint import RunCheckpoint


@dataclass
class DriftCheckResult:
    status: str
    reason: str = ""


def check_checkpoint_drift(checkpoint: RunCheckpoint, ttl_days: int = 30) -> DriftCheckResult:
    if not checkpoint.run_id or not checkpoint.query or not checkpoint.plan:
        return DriftCheckResult("not_resumable", "missing_run_query_or_plan")
    if not checkpoint.pending_steps:
        return DriftCheckResult("already_completed", "no_pending_steps")
    try:
        updated_at = datetime.fromisoformat(checkpoint.updated_at)
    except ValueError:
        return DriftCheckResult("not_resumable", "invalid_updated_at")
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    if (datetime.now(timezone.utc) - updated_at).days > ttl_days:
        return DriftCheckResult("stale_checkpoint", f"older_than_{ttl_days}_days")
    return DriftCheckResult("resumable", "pending_steps_available")
