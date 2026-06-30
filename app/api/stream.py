from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.agent.streaming import stream_pipeline
from app.core.models import ChatRequest

router = APIRouter(tags=["chat"])


@router.get("/chat/stream")
def chat_stream_endpoint(query: str = Query(..., min_length=1)) -> StreamingResponse:
    return StreamingResponse(
        stream_pipeline(ChatRequest(query=query)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
