"""
LangGraph 工具执行层。

LangGraph 只在 Executor 内部编排工具节点；Router 和 Planner 仍由主流程负责。
每个工具节点根据 Planner 输出的 plan 决定执行或跳过，并把执行/跳过元数据写入 state。
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
    tool_calls: list[dict[str, Any]]
    skipped_nodes: list[dict[str, Any]]
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
    return _execute_tool_if_needed(state, "log_tool_node", "log_tool", LogTool())


def execute_config_tool_node(state: AgentGraphState) -> AgentGraphState:
    return _execute_tool_if_needed(state, "config_tool_node", "config_tool", ConfigTool())


def execute_git_tool_node(state: AgentGraphState) -> AgentGraphState:
    return _execute_tool_if_needed(state, "git_tool_node", "git_tool", GitTool())


def execute_rag_tool_node(state: AgentGraphState) -> AgentGraphState:
    return _execute_tool_if_needed(state, "rag_tool_node", "rag_retriever", _RAGRetrieverTool())


def _execute_tool_if_needed(
    state: AgentGraphState,
    node: str,
    tool_name: str,
    tool: Any,
) -> AgentGraphState:
    next_state = _copy_state(state)
    step = _find_plan_step(next_state["plan"], tool_name)
    if step is None:
        next_state["skipped_nodes"].append({
            "node": node,
            "tool_name": tool_name,
            "reason": "tool_not_in_plan",
        })
        return next_state

    start = time.perf_counter()
    try:
        output = tool.run(next_state["query"])
        latency_ms = int((time.perf_counter() - start) * 1000)
        error = output.get("error", "")
        result = {
            "step_id": step.get("id"),
            "action": step.get("action"),
            "node": node,
            "tool": tool_name,
            "tool_name": output.get("tool_name", tool_name),
            "description": step.get("description", ""),
            "status": "failed" if error else "success",
            "result": output.get("result", ""),
            "confidence": output.get("confidence", 0.0),
            "source": output.get("source", ""),
            "documents": output.get("documents", []),
            "error": error,
            "latency_ms": latency_ms,
        }
        next_state["tool_results"].append(result)
        next_state["tool_calls"].append(_tool_call_trace(result))
        if error:
            next_state["errors"].append(f"{tool_name}:{error}")
    except Exception as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)
        error = f"{type(exc).__name__}: {exc}"
        result = {
            "step_id": step.get("id"),
            "action": step.get("action"),
            "node": node,
            "tool": tool_name,
            "tool_name": tool_name,
            "description": step.get("description", ""),
            "status": "failed",
            "result": "",
            "confidence": 0.0,
            "source": "",
            "documents": [],
            "error": error,
            "latency_ms": latency_ms,
        }
        next_state["tool_results"].append(result)
        next_state["tool_calls"].append(_tool_call_trace(result))
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
        "tool_calls": list(state.get("tool_calls", [])),
        "skipped_nodes": list(state.get("skipped_nodes", [])),
        "errors": list(state.get("errors", [])),
    }


def _tool_call_trace(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "node": result.get("node", ""),
        "tool_name": result.get("tool_name", result.get("tool", "")),
        "status": result.get("status", "pending"),
        "latency_ms": result.get("latency_ms", 0),
        "source": result.get("source", ""),
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
