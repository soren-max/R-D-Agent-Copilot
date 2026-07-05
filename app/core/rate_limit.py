"""Local in-memory request rate limiting."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse, Response

from app.core.config import RateLimitSettings, get_rate_limit_settings
from app.core.errors import ErrorCode
from app.core.responses import error_response


@dataclass
class _Bucket:
    window_start: float
    request_count: int = 0


@dataclass
class LocalRateLimiter:
    settings: RateLimitSettings = field(default_factory=get_rate_limit_settings)
    buckets: dict[str, _Bucket] = field(default_factory=dict)

    def allow(self, key: str, now: float | None = None) -> tuple[bool, int]:
        if not self.settings.enabled:
            return True, 0
        now = now if now is not None else time.time()
        bucket = self.buckets.get(key)
        if bucket is None or now - bucket.window_start >= self.settings.window_seconds:
            bucket = _Bucket(window_start=now, request_count=0)
            self.buckets[key] = bucket
        bucket.request_count += 1
        remaining = max(0, self.settings.requests_per_window - bucket.request_count)
        return bucket.request_count <= self.settings.requests_per_window, remaining


_RATE_LIMITER = LocalRateLimiter()


def reset_rate_limiter() -> None:
    """Reset local limiter state. Intended for tests."""

    _RATE_LIMITER.buckets.clear()
    _RATE_LIMITER.settings = get_rate_limit_settings(load_env=False)


def rate_limit_key(request: Request) -> str:
    if request.client and request.client.host:
        return f"ip:{request.client.host}"
    session_id = request.headers.get("x-session-id") or request.headers.get("x-request-id") or "anonymous"
    return f"session:{session_id}"


async def rate_limit_middleware(request: Request, call_next: Callable) -> Response:
    if request.url.path not in {"/chat", "/chat/resume"}:
        return await call_next(request)
    allowed, remaining = _RATE_LIMITER.allow(rate_limit_key(request))
    if not allowed:
        return JSONResponse(
            status_code=429,
            content=error_response(
                ErrorCode.RATE_LIMITED,
                "request rate limit exceeded",
                getattr(request.state, "request_id", "") or request.headers.get("x-request-id", ""),
            ),
            headers={"X-RateLimit-Remaining": str(remaining)},
        )
    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response
