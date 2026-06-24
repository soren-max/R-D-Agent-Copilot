"""
共享数据模型 — Agent 全链路数据契约。

涵盖 Router → Planner → Executor → Trace → Response 各环节。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ── Router ──────────────────────────────────────────────────────────

class RouterResult(BaseModel):
    """意图分类结果。"""

    type: str = Field(description="意图类型：simple_qa | complex_troubleshooting")
    confidence: float = Field(ge=0.0, le=1.0, description="置信度 0.0 ~ 1.0")
    reason: str = Field(description="分类原因说明")


# ── Planner ─────────────────────────────────────────────────────────

class PlanStep(BaseModel):
    """计划中的单个执行步骤。"""

    id: int = Field(description="步骤序号，从 1 开始")
    action: str = Field(description="动作标识，如 query_logs / check_config")
    tool: str = Field(description="执行此步骤所需的工具名")
    description: str = Field(description="步骤描述，供用户阅读")


class Plan(BaseModel):
    """完整执行计划。"""

    plan_type: str = Field(description="计划类型：simple_qa | troubleshooting_plan")
    steps: list[PlanStep] = Field(default_factory=list, description="执行步骤列表")


# ── Executor ────────────────────────────────────────────────────────

class ToolCallRecord(BaseModel):
    """一次工具调用的完整记录。"""

    step_id: int
    action: str
    tool: str
    description: str
    result: str = ""
    confidence: float = 0.0
    latency_ms: int = 0
    status: str = "pending"  # pending | success | skipped | error


# ── Trace ───────────────────────────────────────────────────────────

class TraceStep(BaseModel):
    """Trace 中的单个阶段记录。"""

    stage: str = Field(description="阶段名：router | planner | executor")
    output: str = Field(description="该阶段的摘要输出")
    latency_ms: int = Field(default=0, description="该阶段耗时（毫秒）")
    tool_calls: list[str] = Field(default_factory=list, description="executor 阶段使用的工具列表")


class TraceData(BaseModel):
    """全链路追踪数据。"""

    trace_id: str = Field(description="唯一追踪 ID")
    steps: list[TraceStep] = Field(default_factory=list, description="各阶段记录")
    final_answer: str = Field(default="", description="最终回答")


# ── API ─────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """聊天请求。"""

    query: str = Field(..., min_length=1, description="用户输入的问题")


class ChatResponse(BaseModel):
    """聊天响应。"""

    answer: str = Field(description="最终回答（中文）")
    route: RouterResult = Field(description="Router 分类结果")
    plan: Plan = Field(description="Planner 生成计划")
    tool_results: list[ToolCallRecord] = Field(
        default_factory=list, description="工具执行结果列表"
    )
    trace: TraceData = Field(description="全链路追踪数据")
