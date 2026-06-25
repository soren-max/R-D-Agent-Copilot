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
    node: str = ""
    tool: str
    tool_name: str = ""
    description: str
    result: str = ""
    confidence: float = 0.0
    source: str = ""
    documents: list[dict[str, Any]] = Field(default_factory=list)
    error: str = ""
    retry_count: int = 0
    latency_ms: int = 0
    status: str = "pending"  # pending | success | skipped | failed


# ── Trace ───────────────────────────────────────────────────────────

class TraceToolCall(BaseModel):
    """Trace 中记录的单个工具调用摘要。"""

    node: str = ""
    tool_name: str
    status: str
    retry_count: int = 0
    error: str = ""
    latency_ms: int = 0
    source: str = ""


class TraceSkippedNode(BaseModel):
    """Trace 中记录的跳过工具节点摘要。"""

    node: str
    tool_name: str
    reason: str


class TraceStep(BaseModel):
    """Trace 中的单个阶段记录。"""

    stage: str = Field(description="阶段名：router | planner | executor | synthesizer")
    engine: str = Field(default="", description="执行引擎，如 langgraph")
    graph_name: str = Field(default="", description="执行图名称")
    output: str = Field(description="该阶段的摘要输出")
    latency_ms: int = Field(default=0, description="该阶段耗时（毫秒）")
    llm_used: bool = Field(default=False, description="synthesizer 阶段是否使用 LLM")
    llm_error: str = Field(default="", description="synthesizer 阶段的 LLM 错误")
    tool_calls: list[TraceToolCall] = Field(
        default_factory=list,
        description="executor 阶段使用的工具调用摘要",
    )
    skipped_nodes: list[TraceSkippedNode] = Field(
        default_factory=list,
        description="executor 阶段跳过的工具节点摘要",
    )
    fallback_used: bool = Field(
        default=False,
        description="executor 阶段是否启用了失败 fallback",
    )


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
    answer_source: str = Field(default="fallback", description="答案来源：llm | fallback")
    llm_used: bool = Field(default=False, description="是否使用 LLM 生成最终答案")
    llm_error: str | None = Field(default=None, description="LLM 不可用或失败原因")
    route: RouterResult = Field(description="Router 分类结果")
    plan: Plan = Field(description="Planner 生成计划")
    tool_results: list[ToolCallRecord] = Field(
        default_factory=list, description="工具执行结果列表"
    )
    trace: TraceData = Field(description="全链路追踪数据")
