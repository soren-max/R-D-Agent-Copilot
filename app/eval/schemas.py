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


class EvaluationResult(BaseModel):
    overall_score: float
    metrics: EvaluationMetrics
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
