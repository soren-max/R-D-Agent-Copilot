"""JSON-backed checkpoint store."""

from __future__ import annotations

import json
import os
from pathlib import Path

from app.resume.checkpoint import RunCheckpoint, utc_now_iso

DEFAULT_CHECKPOINT_FILE = Path("data/checkpoints/runs.json")


class CheckpointStore:
    """Small checkpoint store without new database dependencies."""

    def __init__(self, path: str | Path | None = None) -> None:
        env_path = os.getenv("CHECKPOINT_FILE")
        self.path = Path(path or env_path or DEFAULT_CHECKPOINT_FILE)

    def save(self, checkpoint: RunCheckpoint) -> RunCheckpoint:
        checkpoints = self._read_all()
        checkpoint.updated_at = utc_now_iso()
        checkpoints[checkpoint.run_id] = checkpoint
        self._write_all(checkpoints)
        return checkpoint

    def get(self, run_id: str) -> RunCheckpoint | None:
        return self._read_all().get(run_id)

    def list_recent(self, limit: int = 10) -> list[RunCheckpoint]:
        checkpoints = list(self._read_all().values())
        checkpoints.sort(key=lambda item: item.updated_at, reverse=True)
        return checkpoints[:max(1, limit)]

    def latest_resumable(self) -> RunCheckpoint | None:
        for checkpoint in self.list_recent(limit=50):
            if checkpoint.status == "resumable" and checkpoint.pending_steps:
                return checkpoint
        return None

    def update_status(self, run_id: str, status: str) -> RunCheckpoint | None:
        checkpoint = self.get(run_id)
        if checkpoint is None:
            return None
        checkpoint.status = status
        return self.save(checkpoint)

    def _read_all(self) -> dict[str, RunCheckpoint]:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
        if isinstance(raw, list):
            items = raw
        elif isinstance(raw, dict):
            items = raw.values()
        else:
            items = []
        checkpoints: dict[str, RunCheckpoint] = {}
        for item in items:
            if isinstance(item, dict) and item.get("run_id"):
                checkpoint = RunCheckpoint(**item)
                checkpoints[checkpoint.run_id] = checkpoint
        return checkpoints

    def _write_all(self, checkpoints: dict[str, RunCheckpoint]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            run_id: checkpoint.model_dump()
            for run_id, checkpoint in checkpoints.items()
        }
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
