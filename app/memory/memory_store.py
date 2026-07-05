"""JSON-backed incident memory store."""

from __future__ import annotations

import json
import os
from pathlib import Path

from app.core.logging import log_event
from app.memory.incident_memory import IncidentMemory
from app.memory.retrieval import MemoryRetrievalResult, retrieve_incident_memories

DEFAULT_MEMORY_FILE = Path("data/memory/incidents.json")


class MemoryStore:
    """Small JSON store for v1 incident memories."""

    def __init__(self, path: str | Path | None = None) -> None:
        env_path = os.getenv("INCIDENT_MEMORY_FILE")
        self.path = Path(path or env_path or DEFAULT_MEMORY_FILE)

    def add(self, memory: IncidentMemory) -> IncidentMemory:
        memories = self.list()
        existing_index = next(
            (index for index, item in enumerate(memories) if item.memory_id == memory.memory_id),
            None,
        )
        if existing_index is None:
            memories.append(memory)
        else:
            memories[existing_index] = memory
        self._write(memories)
        log_event(event="incident_memory_saved", stage="incident_memory", message=memory.memory_id)
        return memory

    def list(self) -> list[IncidentMemory]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        return [IncidentMemory(**item) for item in raw if isinstance(item, dict)]

    def get(self, memory_id: str) -> IncidentMemory | None:
        return next((memory for memory in self.list() if memory.memory_id == memory_id), None)

    def query_by_service_or_symptom(
        self,
        query: str,
        service: str | None = None,
        limit: int = 3,
    ) -> list[MemoryRetrievalResult]:
        results = retrieve_incident_memories(self.list(), query=query, service=service, limit=limit)
        log_event(event="incident_memory_retrieved", stage="incident_memory", message=f"hits={len(results)}")
        return results

    def _write(self, memories: list[IncidentMemory]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [memory.model_dump() for memory in memories]
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
