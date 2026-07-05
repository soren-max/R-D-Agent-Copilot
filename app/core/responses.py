"""Unified response helpers and FastAPI production middleware."""

from __future__ import annotations

import json
import uuid
from typing import Any, Callable

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.concurrency import iterate_in_threadpool

from app.core.errors import AppError, ErrorCode
from app.core.logging import log_event, set_request_context

REQUEST_ID_HEADER = "X-Request-ID"
ENVELOPE_HEADER = "X-Response-Envelope"


def success_response(data: Any, request_id: str) -> dict[str, Any]:
    return {"success": True, "data": data, "request_id": request_id}


def error_response(error_code: ErrorCode | str, message: str, request_id: str) -> dict[str, Any]:
    return {
        "success": False,
        "error_code": str(error_code),
        "message": message,
        "request_id": request_id,
    }


async def request_context_middleware(request: Request, call_next: Callable) -> Response:
    request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
    request.state.request_id = request_id
    set_request_context(request_id=request_id)
    try:
        response = await call_next(request)
    except Exception:
        log_event(
            event="request_unhandled_exception",
            stage="api",
            level="ERROR",
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Unhandled request error",
            request_id=request_id,
        )
        raise
    response.headers[REQUEST_ID_HEADER] = request_id
    if _should_wrap_success(request, response):
        body = b"".join([chunk async for chunk in response.body_iterator])
        response.body_iterator = iterate_in_threadpool(iter([body]))
        try:
            data = json.loads(body.decode("utf-8")) if body else None
        except Exception:
            return response
        wrapped = JSONResponse(
            status_code=response.status_code,
            content=success_response(data, request_id),
            headers=dict(response.headers),
        )
        wrapped.headers[REQUEST_ID_HEADER] = request_id
        return wrapped
    return response


def register_exception_handlers(app) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return _json_error(request, exc.error_code, exc.message, exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return _json_error(request, ErrorCode.INVALID_REQUEST, "Invalid request parameters.", 422)

    @app.exception_handler(HTTPException)
    async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
        detail = str(exc.detail or "")
        if detail in {"checkpoint_not_found", "run_not_found"}:
            code = ErrorCode.CHECKPOINT_NOT_FOUND
            message = "Checkpoint or run was not found."
        elif exc.status_code == 429:
            code = ErrorCode.RATE_LIMITED
            message = detail or "Request rate limit exceeded."
        elif exc.status_code in {400, 404, 422}:
            code = ErrorCode.INVALID_REQUEST
            message = detail or "Invalid request."
        else:
            code = ErrorCode.INTERNAL_ERROR
            message = "Request failed."
        return _json_error(request, code, message, exc.status_code)

    @app.exception_handler(TimeoutError)
    async def timeout_error_handler(request: Request, exc: TimeoutError) -> JSONResponse:
        return _json_error(request, ErrorCode.PROVIDER_TIMEOUT, "Provider request timed out.", 504)

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return _json_error(request, ErrorCode.INTERNAL_ERROR, "Internal server error.", 500)


def _json_error(
    request: Request,
    error_code: ErrorCode,
    message: str,
    status_code: int,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "") or request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
    set_request_context(request_id=request_id)
    log_event(
        event="request_error",
        stage="api",
        level="ERROR",
        error_code=error_code,
        message=message,
        request_id=request_id,
    )
    response = JSONResponse(
        status_code=status_code,
        content=error_response(error_code, message, request_id),
    )
    response.headers[REQUEST_ID_HEADER] = request_id
    return response


def _should_wrap_success(request: Request, response: Response) -> bool:
    if request.headers.get(ENVELOPE_HEADER, "").lower() not in {"1", "true", "yes"}:
        return False
    if not 200 <= response.status_code < 300:
        return False
    media_type = response.media_type or response.headers.get("content-type", "")
    if "text/event-stream" in media_type:
        return False
    return "application/json" in media_type
