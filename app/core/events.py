from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_safe(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump()
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return value


def sse_event(event: str, data: dict[str, Any]) -> str:
    payload = {"timestamp": utc_timestamp(), **json_safe(data)}
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
