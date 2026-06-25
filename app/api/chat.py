"""
聊天 API 路由 — POST /chat。

接收用户问题，调用完整 Agent Pipeline，返回结果 + 全链路 Trace。
"""

from __future__ import annotations

from fastapi import APIRouter

from app.agent.pipeline import run_pipeline
from app.core.models import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(body: ChatRequest) -> ChatResponse:
    """
    接收用户问题，依次经过：
      Router → Planner → Executor → Synthesizer → Trace
    返回中文回答 + 全链路追踪数据。
    """
    return run_pipeline(body)
