from typing import Any

from pydantic import BaseModel, Field


class EvaluationInput(BaseModel):
    query: str = Field(default="", description="用户原始问题")
    route: dict[str, Any] = Field(default_factory=dict)
    plan: dict[str, Any] = Field(default_factory=dict)
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
    trace: dict[str, Any] = Field(default_factory=dict)
    answer: str = Field(default="")


class EvaluationMetrics(BaseModel):
    tool_success_rate: float
    trace_completeness: float
    rag_relevance: float
    answer_groundedness: float
    latency_score: float
    evidence_confidence_score: float | None = None


class LatencyBreakdown(BaseModel):
    router_ms: int = 0
    planner_ms: int = 0
    executor_ms: int = 0
    tools_ms: int = 0
    synthesizer_ms: int = 0
    evaluation_ms: int = 0
    total_ms: int = 0
    bottleneck_stage: str = "unknown"
    bottleneck_ms: int = 0


class EvaluationResult(BaseModel):
    overall_score: float
    metrics: EvaluationMetrics
    latency_breakdown: LatencyBreakdown = Field(default_factory=LatencyBreakdown)
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class ContextMetricsV2(BaseModel):
    prompt_chars_before: int = 0
    prompt_chars_after: int = 0
    compression_ratio: float = 1.0
    current_query_preserved: bool = False
    reduced_sections: list[str] = Field(default_factory=list)


class ToolMetricsV2(BaseModel):
    tool_success_rate: float = 0.0
    tool_error_count: int = 0
    tool_blocked_count: int = 0
    partial_success_count: int = 0
    avg_tool_latency_ms: float = 0.0
    tool_status_counts: dict[str, int] = Field(default_factory=dict)


class RagMetricsV2(BaseModel):
    rag_hit_count: int = 0
    source_coverage: float = 0.0
    missing_source_count: int = 0
    grounding_score: float = 0.0


class MemoryMetricsV2(BaseModel):
    memory_hit_count: int = 0
    fresh_memory_count: int = 0
    weak_memory_count: int = 0
    stale_memory_count: int = 0
    memory_used_as_reference_count: int = 0
    memory_misused_as_current_fact_count: int = 0


class ResumeMetricsV2(BaseModel):
    checkpoint_created: bool = False
    resume_success: bool = False
    already_completed_count: int = 0
    stale_checkpoint_count: int = 0
    resumed_completed_steps_count: int = 0
    resumed_pending_steps_count: int = 0
    duplicated_step_count: int = 0


class EvidenceMetricsV2(BaseModel):
    evidence_chain_complete: bool = False
    evidence_refs_count: int = 0
    answer_without_evidence_count: int = 0
    root_cause_supported: bool = False
    fix_steps_supported: bool = False


class ProviderMetricsV2(BaseModel):
    llm_enabled: bool = False
    provider_name: str = ""
    model_name: str = ""
    fallback_used: bool = True
    schema_valid: bool = True
    generation_latency_ms: int = 0
    provider_error_count: int = 0


class EvaluationReportV2(BaseModel):
    run_id: str = ""
    overall: float = 0.0
    context: ContextMetricsV2 = Field(default_factory=ContextMetricsV2)
    tool: ToolMetricsV2 = Field(default_factory=ToolMetricsV2)
    rag: RagMetricsV2 = Field(default_factory=RagMetricsV2)
    memory: MemoryMetricsV2 = Field(default_factory=MemoryMetricsV2)
    resume: ResumeMetricsV2 = Field(default_factory=ResumeMetricsV2)
    evidence: EvidenceMetricsV2 = Field(default_factory=EvidenceMetricsV2)
    provider: ProviderMetricsV2 | None = Field(default_factory=ProviderMetricsV2)
