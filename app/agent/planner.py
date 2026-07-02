"""
任务规划器 — 将 Router 分类结果拆解为可执行步骤。

simple_qa → 单步：retrieve_knowledge
complex_troubleshooting → 四步：query_logs → check_config → analyze_git_diff → retrieve_knowledge
"""

from __future__ import annotations

import json
from typing import Any, Final

from app.core.models import Plan, PlanStep, RouterResult
from app.core.prompt import load_prompt
from app.llms.base import LLMProvider, get_llm_provider

_ALLOWED_TOOLS: Final[set[str]] = {"log_tool", "config_tool", "git_tool", "rag_retriever"}
_STEP_ACTION_BY_TOOL: Final[dict[str, str]] = {
    "log_tool": "query_logs",
    "config_tool": "check_config",
    "git_tool": "analyze_git_diff",
    "rag_retriever": "retrieve_knowledge",
}


class Planner:
    """Router 结果 → Plan。"""

    def __init__(self, llm_provider: LLMProvider | None = None) -> None:
        self.llm_provider = llm_provider or get_llm_provider()
        self.prompt_name = "planner_prompt"
        self.system_prompt, self.prompt_version = load_prompt(self.prompt_name)

    def plan(self, query: str, route_result: RouterResult) -> Plan:
        llm_plan = self._plan_with_llm(query, route_result)
        if llm_plan is not None:
            return llm_plan

        return self._plan_rule_based(query, route_result)

    def _plan_with_llm(self, query: str, route_result: RouterResult) -> Plan | None:
        if not self.llm_provider.is_available():
            return None
        try:
            response = self.llm_provider.generate(
                self.prompt_name,
                self.system_prompt,
                json.dumps({
                    "query": query,
                    "route_result": route_result.model_dump(),
                }, ensure_ascii=False),
            )
            parsed = _parse_planner_json(response.content)
            return _plan_from_parsed(
                parsed,
                prompt_name=self.prompt_name,
                prompt_version=self.prompt_version,
                model=response.model,
                raw_llm_output=response.raw_output,
                fallback_used=False,
            )
        except Exception as exc:
            fallback = self._plan_rule_based(query, route_result)
            fallback.prompt_name = self.prompt_name
            fallback.prompt_version = self.prompt_version
            fallback.error_message = type(exc).__name__
            fallback.fallback_used = True
            return fallback

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


def _parse_planner_json(raw: str) -> dict[str, Any]:
    parsed = json.loads(_strip_json(raw))
    if not isinstance(parsed, dict):
        raise ValueError("planner output must be a JSON object")
    task_type = str(parsed.get("task_type", "")).strip() or "unknown"
    steps = parsed.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("planner steps must be a non-empty list")
    normalized_steps: list[dict[str, str]] = []
    for step in steps:
        if not isinstance(step, dict):
            raise ValueError("planner step must be an object")
        tool = str(step.get("tool", "")).strip()
        if tool not in _ALLOWED_TOOLS:
            raise ValueError("planner step uses unsupported tool")
        step_name = str(step.get("step_name", "")).strip() or _STEP_ACTION_BY_TOOL[tool]
        normalized_steps.append({
            "step_name": step_name,
            "tool": tool,
            "input": str(step.get("input", "")).strip(),
            "expected_output": str(step.get("expected_output", "")).strip(),
        })
    if not any(step["tool"] == "rag_retriever" for step in normalized_steps):
        normalized_steps.append({
            "step_name": "retrieve_knowledge",
            "tool": "rag_retriever",
            "input": "用户问题",
            "expected_output": "相关知识库片段",
        })
    return {"task_type": task_type, "steps": normalized_steps}


def _plan_from_parsed(
    parsed: dict[str, Any],
    prompt_name: str,
    prompt_version: str,
    model: str,
    raw_llm_output: str,
    fallback_used: bool,
) -> Plan:
    task_type = str(parsed["task_type"])
    plan_type = "simple_qa" if task_type == "knowledge_qa" else "troubleshooting_plan"
    steps = [
        PlanStep(
            id=index,
            action=_STEP_ACTION_BY_TOOL[step["tool"]],
            tool=step["tool"],
            description=step["expected_output"] or step["step_name"],
            step_name=step["step_name"],
            input=step["input"],
            expected_output=step["expected_output"],
        )
        for index, step in enumerate(parsed["steps"], start=1)
    ]
    return Plan(
        plan_type=plan_type,
        task_type=task_type,
        steps=steps,
        prompt_name=prompt_name,
        prompt_version=prompt_version,
        model=model,
        raw_llm_output=raw_llm_output,
        parsed_output=parsed,
        fallback_used=fallback_used,
    )


def _strip_json(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return text.strip()
