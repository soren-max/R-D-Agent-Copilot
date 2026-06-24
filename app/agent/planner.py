"""
任务规划器 — 将 Router 分类结果拆解为可执行步骤。

simple_qa → 单步：retrieve_knowledge (tool=none)
complex_troubleshooting → 三步：query_logs → check_config → analyze_git_diff
"""

from __future__ import annotations

from app.core.models import Plan, PlanStep, RouterResult


class Planner:
    """Router 结果 → Plan。"""

    def plan(self, query: str, route_result: RouterResult) -> Plan:
        intent_type = route_result.type

        if intent_type == "complex_troubleshooting":
            return self._plan_troubleshooting(query)
        else:
            return self._plan_simple_qa(query)

    def _plan_simple_qa(self, query: str) -> Plan:
        return Plan(
            plan_type="simple_qa",
            steps=[
                PlanStep(id=1, action="retrieve_knowledge", tool="none",
                         description=f"根据已有知识解释「{query}」"),
            ],
        )

    def _plan_troubleshooting(self, query: str) -> Plan:
        return Plan(
            plan_type="troubleshooting_plan",
            steps=[
                PlanStep(id=1, action="query_logs", tool="log_tool",
                         description=f"查询相关服务日志，排查「{query}」中的异常"),
                PlanStep(id=2, action="check_config", tool="config_tool",
                         description="检查服务配置是否正确"),
                PlanStep(id=3, action="analyze_git_diff", tool="git_tool",
                         description="分析最近代码变更，寻找引入问题的变更"),
            ],
        )
