"""Tool gateway request schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolGatewayRequest(BaseModel):
    """Input passed through the tool gateway."""

    tool_name: str
    params: dict[str, Any] = Field(default_factory=dict)
