"""Context metadata models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ContextMetadata(BaseModel):
    """Context compression metadata recorded into trace."""

    total_chars_before: int = 0
    total_chars_after: int = 0
    compression_ratio: float = 1.0
    section_char_counts: dict[str, int] = Field(default_factory=dict)
    reduced_sections: list[str] = Field(default_factory=list)
    memory_hit_count: int = 0
    fresh_memory_count: int = 0
    stale_memory_count: int = 0
