"""Structured context sections passed to the Answer Synthesizer."""

from __future__ import annotations

from pydantic import BaseModel, Field

from apps.api.app.context.metadata import ContextMetadata


class ContextSection(BaseModel):
    """One named context block with accounting metadata."""

    name: str
    content: str = ""
    chars_before: int = 0
    chars_after: int = 0
    reduced: bool = False


class ContextPackage(BaseModel):
    """Layered context package for final answer generation."""

    sections: list[ContextSection] = Field(default_factory=list)
    metadata: ContextMetadata = Field(default_factory=ContextMetadata)

    def section(self, name: str) -> ContextSection | None:
        return next((section for section in self.sections if section.name == name), None)

    def as_prompt_payload(self) -> dict[str, str]:
        return {section.name: section.content for section in self.sections}
