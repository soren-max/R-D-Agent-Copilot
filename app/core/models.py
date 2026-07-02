"""
共享数据模型 — Agent 全链路数据契约。

涵盖 Router → Planner → Executor → Trace → Response 各环节。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.evidence.schemas import EvidenceChain
from app.eval.schemas import EvaluationResult


# ── Router ──────────────────────────────────────────────────────────

class RouterResult(BaseModel):
    """意图分类结果。"""

    type: str = Field(description="意图类型：simple_qa | complex_troubleshooting")
    intent: str = Field(default="", description="v0.2.0 意图：knowledge_qa | log_analysis | config_diff | git_change | unknown")
    confidence: float = Field(ge=0.0, le=1.0, description="置信度 0.0 ~ 1.0")
    reason: str = Field(description="分类原因说明")
    prompt_name: str = ""
    prompt_version: str = ""
    model: str = ""
    raw_llm_output: str = ""
    parsed_output: dict[str, Any] | None = None
    error_message: str = ""
    fallback_used: bool = False

    @model_validator(mode="after")
    def sync_type_and_intent(self) -> "RouterResult":
        if not self.intent:
            self.intent = "knowledge_qa" if self.type == "simple_qa" else "log_analysis"
        if not self.type:
            self.type = "simple_qa" if self.intent == "knowledge_qa" else "complex_troubleshooting"
        return self


# ── Planner ─────────────────────────────────────────────────────────

class PlanStep(BaseModel):
    """计划中的单个执行步骤。"""

    id: int = Field(description="步骤序号，从 1 开始")
    action: str = Field(description="动作标识，如 query_logs / check_config")
    tool: str = Field(description="执行此步骤所需的工具名")
    description: str = Field(description="步骤描述，供用户阅读")
    step_name: str = Field(default="", description="v0.2.0 结构化步骤名称")
    input: str = Field(default="", description="v0.2.0 步骤输入")
    expected_output: str = Field(default="", description="v0.2.0 期望输出")

    @model_validator(mode="after")
    def sync_step_fields(self) -> "PlanStep":
        if not self.step_name:
            self.step_name = self.action
        if not self.description:
            self.description = self.expected_output or self.step_name
        if not self.action:
            self.action = self.step_name
        return self


class Plan(BaseModel):
    """完整执行计划。"""

    plan_type: str = Field(description="计划类型：simple_qa | troubleshooting_plan")
    task_type: str = Field(default="", description="v0.2.0 任务类型")
    steps: list[PlanStep] = Field(default_factory=list, description="执行步骤列表")
    prompt_name: str = ""
    prompt_version: str = ""
    model: str = ""
    raw_llm_output: str = ""
    parsed_output: dict[str, Any] | None = None
    error_message: str = ""
    fallback_used: bool = False

    @model_validator(mode="after")
    def sync_plan_fields(self) -> "Plan":
        if not self.task_type:
            self.task_type = self.plan_type
        if not self.plan_type:
            self.plan_type = "simple_qa" if self.task_type == "knowledge_qa" else "troubleshooting_plan"
        return self


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
    rag_metadata: dict[str, Any] = Field(default_factory=dict)
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
    retrieval_top_k: int | None = None
    score_threshold: float | None = None
    retrieved_count: int | None = None
    grounding_status: str = ""
    retrieval_latency_ms: int | None = None
    retrieval_type: str = ""
    fallback_used: bool | None = None


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
    prompt_version: str = Field(
        default="",
        description="synthesizer 阶段使用的 prompt 版本",
    )
    prompt_name: str = Field(default="", description="v0.2.0 prompt 名称")
    model: str = Field(default="", description="v0.2.0 LLM 模型")
    raw_llm_output: str = Field(default="", description="v0.2.0 原始 LLM 输出")
    parsed_output: dict[str, Any] | None = Field(default=None, description="v0.2.0 解析后的结构化输出")
    error_message: str = Field(default="", description="v0.2.0 LLM 或解析错误")
    llm_usage: dict[str, Any] | None = Field(
        default=None,
        description="synthesizer 阶段的 LLM token/cost 用量",
    )
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
    overall_score: float | None = Field(
        default=None,
        description="evaluation 阶段的总体评分",
    )
    evaluation_error: str = Field(
        default="",
        description="evaluation 阶段的脱敏错误标记",
    )
    overall_confidence: float | None = Field(
        default=None,
        description="evidence 阶段的总体置信度",
    )
    evidence_count: int | None = Field(
        default=None,
        description="evidence 阶段生成的证据数量",
    )
    retrieval_top_k: int | None = Field(
        default=None,
        description="RAG 检索 top_k 参数",
    )
    score_threshold: float | None = Field(
        default=None,
        description="RAG 检索分数阈值",
    )
    retrieved_count: int | None = Field(
        default=None,
        description="RAG 返回文档数量",
    )
    grounding_status: str = Field(
        default="",
        description="RAG grounding 状态",
    )
    retrieval_latency_ms: int | None = Field(
        default=None,
        description="RAG 检索耗时",
    )
    query: str = Field(default="", description="v0.3.0 RAG 查询")
    retrieved_chunks: list[dict[str, Any]] = Field(
        default_factory=list,
        description="v0.3.0 检索到的知识库 chunks",
    )
    rewritten_queries: list[str] = Field(
        default_factory=list,
        description="v0.3.1 Query Rewrite 后的查询列表",
    )
    query_expansions: list[str] = Field(
        default_factory=list,
        description="v0.3.1 Query Rewrite 扩展词",
    )
    evidence: list[dict[str, Any]] = Field(
        default_factory=list,
        description="v0.3.0 grounding evidence",
    )
    no_evidence_reason: str = Field(
        default="",
        description="v0.3.0 无证据原因",
    )


class TraceData(BaseModel):
    """全链路追踪数据。"""

    trace_id: str = Field(description="唯一追踪 ID")
    steps: list[TraceStep] = Field(default_factory=list, description="各阶段记录")
    final_answer: str = Field(default="", description="最终回答")
    persistence_error: str | None = Field(
        default=None,
        description="持久化失败时的脱敏错误标记",
    )
    evaluation_error: str | None = Field(
        default=None,
        description="评估失败时的脱敏错误标记",
    )


# ── API ─────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """聊天请求。"""

    query: str = Field(..., min_length=1, description="用户输入的问题")


class ChatResponse(BaseModel):
    """聊天响应。"""

    run_id: str = Field(default="", description="持久化 Run ID，与 trace_id 保持一致")
    answer: str = Field(description="最终回答（中文）")
    answer_source: str = Field(default="fallback", description="答案来源：llm | fallback")
    llm_used: bool = Field(default=False, description="是否使用 LLM 生成最终答案")
    llm_error: str | None = Field(default=None, description="LLM 不可用或失败原因")
    llm_usage: dict[str, Any] | None = Field(
        default=None,
        description="LLM token 用量与成本估算",
    )
    route: RouterResult = Field(description="Router 分类结果")
    plan: Plan = Field(description="Planner 生成计划")
    tool_results: list[ToolCallRecord] = Field(
        default_factory=list, description="工具执行结果列表"
    )
    trace: TraceData = Field(description="全链路追踪数据")
    evaluation: EvaluationResult | None = Field(
        default=None,
        description="Agent 执行质量评估结果",
    )
    evidence_chain: EvidenceChain | None = Field(
        default=None,
        description="证据链与置信度结果",
    )
