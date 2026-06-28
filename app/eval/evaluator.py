from typing import Any

from pydantic import BaseModel

from app.eval.schemas import EvaluationInput, EvaluationMetrics, EvaluationResult, LatencyBreakdown


CORE_TRACE_STAGES = {"router", "planner", "executor", "synthesizer"}
GROUNDEDNESS_KEYWORDS = [
    "日志",
    "配置",
    "Git",
    "代码变更",
    "知识库",
    "trace_id",
    "timeout",
    "500",
    "工具证据",
]
WEIGHTS = {
    "tool_success_rate": 0.25,
    "trace_completeness": 0.25,
    "rag_relevance": 0.15,
    "answer_groundedness": 0.25,
    "latency_score": 0.10,
}


class RuleBasedEvaluator:
    """Deterministic Evaluation v1 scorer."""

    def evaluate(self, payload: dict[str, Any] | EvaluationInput | BaseModel) -> EvaluationResult:
        data = self._normalize_input(payload)
        metrics = EvaluationMetrics(
            tool_success_rate=self.score_tool_success_rate(data.tool_results),
            trace_completeness=self.score_trace_completeness(data.trace),
            rag_relevance=self.score_rag_relevance(data.route, data.tool_results),
            answer_groundedness=self.score_answer_groundedness(data.answer),
            latency_score=self.score_latency(data.trace),
        )
        issues, suggestions = self._build_feedback(metrics)

        return EvaluationResult(
            overall_score=self._overall_score(metrics),
            metrics=metrics,
            latency_breakdown=self.build_latency_breakdown(data.trace, data.tool_results),
            issues=issues,
            suggestions=suggestions,
        )

    def score_tool_success_rate(self, tool_results: list[dict[str, Any]]) -> float:
        executed_tools = [
            result
            for result in tool_results
            if self._get(result, "tool") != "none" and self._get(result, "status") != "skipped"
        ]
        if not executed_tools:
            return 0.0

        success_count = sum(1 for result in executed_tools if self._get(result, "status") == "success")
        return round(success_count / len(executed_tools), 2)

    def score_trace_completeness(self, trace: dict[str, Any]) -> float:
        stages = {
            self._get(step, "stage")
            for step in self._get(trace, "steps", [])
            if self._get(step, "stage")
        }
        present_count = len(CORE_TRACE_STAGES.intersection(stages))
        return round(present_count / len(CORE_TRACE_STAGES), 2)

    def score_rag_relevance(self, route: dict[str, Any], tool_results: list[dict[str, Any]]) -> float:
        rag_result = self._find_rag_result(tool_results)
        route_type = self._get(route, "type", "")

        if rag_result is None:
            return 0.0 if route_type == "simple_qa" else 0.5

        documents = self._get(rag_result, "documents", [])
        if documents:
            return 0.9
        return 0.3

    def score_answer_groundedness(self, answer: str) -> float:
        if not answer:
            return 0.0

        lower_answer = answer.lower()
        hit_count = sum(
            1
            for keyword in GROUNDEDNESS_KEYWORDS
            if keyword.lower() in lower_answer
        )
        return round(min(hit_count / 4, 1.0), 2)

    def score_latency(self, trace: dict[str, Any]) -> float:
        latency = self._get(trace, "total_latency_ms")
        if latency is None:
            step_latencies = [
                self._get(step, "latency_ms")
                for step in self._get(trace, "steps", [])
                if self._get(step, "latency_ms") is not None
            ]
            if step_latencies:
                latency = sum(step_latencies)

        if latency is None:
            return 0.5
        if latency <= 1000:
            return 1.0
        if latency <= 3000:
            return 0.8
        if latency <= 8000:
            return 0.6
        return 0.3

    def build_latency_breakdown(
        self,
        trace: dict[str, Any],
        tool_results: list[dict[str, Any]],
    ) -> LatencyBreakdown:
        stage_latencies = self._stage_latencies(trace)
        tools_ms = sum(
            self._coerce_ms(self._get(result, "latency_ms"))
            for result in tool_results
            if self._get(result, "tool") != "none" and self._get(result, "status") != "skipped"
        )
        total_ms = self._coerce_ms(self._get(trace, "total_latency_ms"))
        if total_ms == 0:
            total_ms = sum(stage_latencies.values())

        bottleneck_candidates = {
            "router": stage_latencies.get("router", 0),
            "planner": stage_latencies.get("planner", 0),
            "executor": stage_latencies.get("executor", 0),
            "tools": tools_ms,
            "synthesizer": stage_latencies.get("synthesizer", 0),
            "evaluation": stage_latencies.get("evaluation", 0),
        }
        bottleneck_stage, bottleneck_ms = max(
            bottleneck_candidates.items(),
            key=lambda item: item[1],
        )
        if bottleneck_ms <= 0:
            bottleneck_stage = "unknown"

        return LatencyBreakdown(
            router_ms=stage_latencies.get("router", 0),
            planner_ms=stage_latencies.get("planner", 0),
            executor_ms=stage_latencies.get("executor", 0),
            tools_ms=tools_ms,
            synthesizer_ms=stage_latencies.get("synthesizer", 0),
            evaluation_ms=stage_latencies.get("evaluation", 0),
            total_ms=total_ms,
            bottleneck_stage=bottleneck_stage,
            bottleneck_ms=bottleneck_ms,
        )

    def _overall_score(self, metrics: EvaluationMetrics) -> float:
        score = (
            metrics.tool_success_rate * WEIGHTS["tool_success_rate"]
            + metrics.trace_completeness * WEIGHTS["trace_completeness"]
            + metrics.rag_relevance * WEIGHTS["rag_relevance"]
            + metrics.answer_groundedness * WEIGHTS["answer_groundedness"]
            + metrics.latency_score * WEIGHTS["latency_score"]
        )
        return round(score, 2)

    def _build_feedback(self, metrics: EvaluationMetrics) -> tuple[list[str], list[str]]:
        issues: list[str] = []
        suggestions: list[str] = []

        if metrics.tool_success_rate < 1.0:
            issues.append("存在工具调用失败或未成功完成")
            suggestions.append("检查失败工具的错误信息和重试策略")
        if metrics.trace_completeness < 1.0:
            issues.append("Trace 缺少核心执行阶段")
            suggestions.append("确保 Router、Planner、Executor 和 Synthesizer 阶段都被记录")
        if metrics.rag_relevance < 0.8:
            issues.append("RAG 检索结果较少")
            suggestions.append("可以补充更多知识库文档，提高检索覆盖率")
        if metrics.answer_groundedness < 0.5:
            issues.append("回答中的工具证据引用不足")
            suggestions.append("回答中应明确引用日志、配置、Git 变更或知识库证据")
        if metrics.latency_score < 0.8:
            issues.append("执行耗时偏高")
            suggestions.append("可以检查工具调用耗时和 LangGraph 执行链路")

        return issues, suggestions

    def _find_rag_result(self, tool_results: list[dict[str, Any]]) -> dict[str, Any] | None:
        for result in tool_results:
            tool = self._get(result, "tool", "")
            tool_name = self._get(result, "tool_name", "")
            if tool == "rag_retriever" or tool_name == "rag_retriever":
                return result
        return None

    def _normalize_input(self, payload: dict[str, Any] | EvaluationInput | BaseModel) -> EvaluationInput:
        if isinstance(payload, EvaluationInput):
            return payload
        if isinstance(payload, BaseModel):
            payload = payload.model_dump()

        return EvaluationInput(
            query=self._get(payload, "query", ""),
            route=self._as_dict(self._get(payload, "route", {})),
            plan=self._as_dict(self._get(payload, "plan", {})),
            tool_results=[self._as_dict(result) for result in self._get(payload, "tool_results", [])],
            trace=self._as_dict(self._get(payload, "trace", {})),
            answer=self._get(payload, "answer", ""),
        )

    def _stage_latencies(self, trace: dict[str, Any]) -> dict[str, int]:
        latencies: dict[str, int] = {}
        for step in self._get(trace, "steps", []):
            stage = self._get(step, "stage")
            if not stage:
                continue
            latencies[stage] = latencies.get(stage, 0) + self._coerce_ms(self._get(step, "latency_ms"))
        return latencies

    def _coerce_ms(self, value: Any) -> int:
        if isinstance(value, bool):
            return 0
        if isinstance(value, (int, float)):
            return max(0, int(value))
        return 0

    def _as_dict(self, value: Any) -> dict[str, Any]:
        if isinstance(value, BaseModel):
            return value.model_dump()
        if isinstance(value, dict):
            return value
        return {}

    def _get(self, source: Any, key: str, default: Any = None) -> Any:
        if isinstance(source, BaseModel):
            return getattr(source, key, default)
        if isinstance(source, dict):
            return source.get(key, default)
        return default
