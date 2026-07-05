"""
任务规划器 — 将 Router 分类结果拆解为可执行步骤。

simple_qa → 单步：retrieve_knowledge
complex_troubleshooting → 四步：query_logs → check_config → analyze_git_diff → retrieve_knowledge
"""

from __future__ import annotations

from typing import Final

from app.core.models import Plan, PlanStep, RouterResult

_ALLOWED_TOOLS: Final[set[str]] = {"log_tool", "config_tool", "git_tool", "rag_retriever"}
_STEP_ACTION_BY_TOOL: Final[dict[str, str]] = {
    "log_tool": "query_logs",
    "config_tool": "check_config",
    "git_tool": "analyze_git_diff",
    "rag_retriever": "retrieve_knowledge",
}


class Planner:
    """Router 结果 → deterministic Plan。

    ``llm_provider`` is accepted only as a deprecated compatibility argument.
    Planner must never call an LLM or accept model-selected tools.
    """

    def __init__(self, llm_provider: object | None = None) -> None:
        self.legacy_llm_provider_ignored = llm_provider is not None

    def plan(self, query: str, route_result: RouterResult) -> Plan:
        return self._plan_rule_based(query, route_result)

    def _plan_rule_based(self, query: str, route_result: RouterResult) -> Plan:
        intent_type = route_result.type

        if intent_type == "complex_troubleshooting":
            return self._plan_troubleshooting(query, route_result.intent)
        else:
            return self._plan_simple_qa(query)

    def _plan_simple_qa(self, query: str) -> Plan:
        return Plan(
            plan_type="simple_qa",
            task_type="knowledge_qa",
            steps=[
                PlanStep(id=1, action="retrieve_knowledge", tool="rag_retriever",
                         description="从本地知识库检索相关说明",
                         step_name="retrieve_knowledge",
                         input=query,
                         expected_output="相关知识库片段"),
            ],
        )

    def _plan_troubleshooting(self, query: str, intent: str = "log_analysis") -> Plan:
        primary_steps: list[PlanStep]
        if intent == "config_diff":
            primary_steps = [
                PlanStep(id=1, action="check_config", tool="config_tool",
                         description="检查服务配置是否正确",
                         step_name="check_config",
                         input=query,
                         expected_output="配置差异和风险配置项"),
            ]
        elif intent == "deployment_issue":
            primary_steps = [
                PlanStep(id=1, action="query_logs", tool="log_tool",
                         description=f"查询部署或启动相关日志，排查「{query}」中的失败原因",
                         step_name="query_logs",
                         input=query,
                         expected_output="部署失败、启动失败或端口冲突日志"),
                PlanStep(id=2, action="check_config", tool="config_tool",
                         description="检查端口、健康检查和运行时配置",
                         step_name="check_config",
                         input=query,
                         expected_output="部署配置和健康检查配置差异"),
                PlanStep(id=3, action="analyze_git_diff", tool="git_tool",
                         description="分析最近发布涉及的代码变更",
                         step_name="analyze_git_diff",
                         input=query,
                         expected_output="近期发布变更摘要"),
            ]
        elif intent == "safety_risk":
            primary_steps = [
                PlanStep(id=1, action="retrieve_knowledge", tool="rag_retriever",
                         description="检索安全边界和风险处置知识，避免执行危险操作",
                         step_name="retrieve_knowledge",
                         input=query,
                         expected_output="安全风险说明和受控排查建议"),
            ]
        elif intent == "git_change":
            primary_steps = [
                PlanStep(id=1, action="analyze_git_diff", tool="git_tool",
                         description="分析最近代码变更，寻找引入问题的变更",
                         step_name="analyze_git_diff",
                         input=query,
                         expected_output="相关 Git 提交和变更摘要"),
            ]
        else:
            primary_steps = [
                PlanStep(id=1, action="query_logs", tool="log_tool",
                         description=f"查询相关服务日志，排查「{query}」中的异常",
                         step_name="query_logs",
                         input=query,
                         expected_output="错误日志和异常摘要"),
                PlanStep(id=2, action="check_config", tool="config_tool",
                         description="检查服务配置是否正确",
                         step_name="check_config",
                         input=query,
                         expected_output="配置差异和风险配置项"),
                PlanStep(id=3, action="analyze_git_diff", tool="git_tool",
                         description="分析最近代码变更，寻找引入问题的变更",
                         step_name="analyze_git_diff",
                         input=query,
                         expected_output="相关 Git 提交和变更摘要"),
            ]
        rag_id = len(primary_steps) + 1
        if any(step.tool == "rag_retriever" for step in primary_steps):
            return Plan(
                plan_type="troubleshooting_plan",
                task_type=intent or "log_analysis",
                steps=primary_steps,
            )
        return Plan(
            plan_type="troubleshooting_plan",
            task_type=intent or "log_analysis",
            steps=primary_steps + [
                PlanStep(id=rag_id, action="retrieve_knowledge", tool="rag_retriever",
                         description="从本地知识库检索排障知识补充",
                         step_name="retrieve_knowledge",
                         input=query,
                         expected_output="相关排障知识片段"),
            ],
        )
