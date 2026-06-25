"""
LangGraph 执行层骨架。

当前图只作为 Day4 编排实验入口，不替换现有 Executor 和 /chat 主流程。
节点按固定顺序执行，并在节点内部根据 Planner 输出判断是否需要调用工具。
"""

from __future__ import annotations

import time
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.rag.retriever import LocalKnowledgeRetriever
from app.tools.config_tool import ConfigTool
from app.tools.git_tool import GitTool
from app.tools.log_tool import LogTool


class AgentGraphState(TypedDict):
    query: str
    plan: dict[str, Any]
    tool_results: list[dict[str, Any]]
    errors: list[str]


def build_execution_graph():
    """构建并 compile LangGraph 执行图。"""
    graph = StateGraph(AgentGraphState)
    graph.add_node("log_tool_node", execute_log_tool_node)
    graph.add_node("config_tool_node", execute_config_tool_node)
    graph.add_node("git_tool_node", execute_git_tool_node)
    graph.add_node("rag_tool_node", execute_rag_tool_node)

    graph.add_edge(START, "log_tool_node")
    graph.add_edge("log_tool_node", "config_tool_node")
    graph.add_edge("config_tool_node", "git_tool_node")
    graph.add_edge("git_tool_node", "rag_tool_node")
    graph.add_edge("rag_tool_node", END)
    return graph.compile()


def execute_log_tool_node(state: AgentGraphState) -> AgentGraphState:
    return _execute_tool_if_needed(state, "log_tool", LogTool())


def execute_config_tool_node(state: AgentGraphState) -> AgentGraphState:
    return _execute_tool_if_needed(state, "config_tool", ConfigTool())


def execute_git_tool_node(state: AgentGraphState) -> AgentGraphState:
    return _execute_tool_if_needed(state, "git_tool", GitTool())


def execute_rag_tool_node(state: AgentGraphState) -> AgentGraphState:
    return _execute_tool_if_needed(state, "rag_retriever", _RAGRetrieverTool())


def _execute_tool_if_needed(state: AgentGraphState, tool_name: str, tool: Any) -> AgentGraphState:
    next_state = _copy_state(state)
    step = _find_plan_step(next_state["plan"], tool_name)
    if step is None:
        return next_state

    start = time.perf_counter()
    try:
        output = tool.run(next_state["query"])
        latency_ms = int((time.perf_counter() - start) * 1000)
        error = output.get("error", "")
        next_state["tool_results"].append({
            "step_id": step.get("id"),
            "action": step.get("action"),
            "tool_name": output.get("tool_name", tool_name),
            "status": "failed" if error else "success",
            "result": output.get("result", ""),
            "confidence": output.get("confidence", 0.0),
            "source": output.get("source", ""),
            "documents": output.get("documents", []),
            "error": error,
            "latency_ms": latency_ms,
        })
        if error:
            next_state["errors"].append(f"{tool_name}:{error}")
    except Exception as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)
        error = f"{type(exc).__name__}: {exc}"
        next_state["tool_results"].append({
            "step_id": step.get("id"),
            "action": step.get("action"),
            "tool_name": tool_name,
            "status": "failed",
            "result": "",
            "confidence": 0.0,
            "source": "",
            "documents": [],
            "error": error,
            "latency_ms": latency_ms,
        })
        next_state["errors"].append(f"{tool_name}:{error}")

    return next_state


def _find_plan_step(plan: dict[str, Any], tool_name: str) -> dict[str, Any] | None:
    for step in plan.get("steps", []):
        if step.get("tool") == tool_name:
            return step
    return None


def _copy_state(state: AgentGraphState) -> AgentGraphState:
    return {
        "query": state["query"],
        "plan": state["plan"],
        "tool_results": list(state.get("tool_results", [])),
        "errors": list(state.get("errors", [])),
    }


class _RAGRetrieverTool:
    name = "rag_retriever"

    def __init__(self):
        self._retriever = LocalKnowledgeRetriever()

    def run(self, query: str) -> dict[str, Any]:
        retrieval = self._retriever.retrieve(query, top_k=3)
        documents = retrieval.get("documents", [])
        source = ",".join(dict.fromkeys(doc["source"] for doc in documents))

        if error := retrieval.get("error"):
            return {
                "tool_name": self.name,
                "result": "知识库中未检索到直接相关内容。",
                "confidence": 0.0,
                "source": source or "data/docs",
                "documents": [],
                "error": error,
            }

        return {
            "tool_name": self.name,
            "result": f"检索到 {len(documents)} 条相关知识片段",
            "confidence": max((doc["score"] for doc in documents), default=0.0),
            "source": source,
            "documents": documents,
        }
