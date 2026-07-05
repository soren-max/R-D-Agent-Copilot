"""
LangGraph 工具执行层。

LangGraph 只在 Executor 内部编排工具节点；Router 和 Planner 仍由主流程负责。
每个工具节点根据 Planner 输出的 plan 决定执行或跳过，并把执行/跳过元数据写入 state。
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.rag.retriever import LocalKnowledgeRetriever
from app.tools.config_tool import ConfigTool
from app.tools.gateway import ToolGateway
from app.tools.git_tool import GitTool
from app.tools.log_tool import LogTool
from app.tools.result import StandardToolResult
from apps.api.app.rag.retriever import KeywordRetriever


class AgentGraphState(TypedDict):
    query: str
    plan: dict[str, Any]
    tool_results: list[dict[str, Any]]
    tool_calls: list[dict[str, Any]]
    skipped_nodes: list[dict[str, Any]]
    fallback_used: bool
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

    output, latency_ms, retry_count = _run_tool_with_retry(tool, next_state["query"])
    error = output.get("error", "")
    status = output.get("status") or ("failed" if error else "success")
    result = {
        "step_id": step.get("id"),
        "action": step.get("action"),
        "node": node,
        "tool": tool_name,
        "tool_name": output.get("tool_name", tool_name),
        "description": step.get("description", ""),
        "status": status,
        "result": output.get("result", ""),
        "confidence": output.get("confidence", 0.0),
        "source": output.get("source", ""),
        "documents": output.get("documents", []),
        "rag_metadata": output.get("rag_metadata", {}),
        "error": error,
        "retry_count": retry_count,
        "latency_ms": latency_ms,
        "gateway_metadata": output.get("gateway_metadata", {}),
    }
    next_state["tool_results"].append(result)
    next_state["tool_calls"].append(_tool_call_trace(result))
    if status == "failed":
        next_state["fallback_used"] = True
    if error:
        next_state["errors"].append(f"{tool_name}:{error}")

    return next_state


def _run_tool_with_retry(tool: Any, query: str) -> tuple[dict[str, Any], int, int]:
    max_retry = 1
    retry_count = 0
    total_latency_ms = 0

    output, latency_ms = _run_tool_once(tool, query)
    total_latency_ms += latency_ms

    while retry_count < max_retry and _should_retry(output):
        retry_count += 1
        output, latency_ms = _run_tool_once(tool, query)
        total_latency_ms += latency_ms

    return output, total_latency_ms, retry_count


def _run_tool_once(tool: Any, query: str) -> tuple[dict[str, Any], int]:
    gateway_result = ToolGateway().execute(
        getattr(tool, "name", ""),
        {"query": query},
        tool=tool,
    )
    return _gateway_result_to_tool_output(gateway_result), gateway_result.latency_ms


def _gateway_result_to_tool_output(gateway_result: StandardToolResult) -> dict[str, Any]:
    raw_output = dict(gateway_result.metadata.get("raw_output", {}))
    output = {
        "tool_name": raw_output.get("tool_name", gateway_result.tool_name),
        "status": gateway_result.legacy_status(),
        "result": raw_output.get("result", ""),
        "confidence": raw_output.get("confidence", 0.0),
        "source": raw_output.get("source", ""),
        "documents": raw_output.get("documents", []),
        "rag_metadata": raw_output.get("rag_metadata", {}),
        "error": raw_output.get("error", ""),
        "gateway_metadata": gateway_result.model_dump(),
    }
    if gateway_result.status in {"error", "blocked"}:
        output["error"] = gateway_result.error_code or output["error"]
    return output


def _should_retry(output: dict[str, Any]) -> bool:
    status = output.get("status") or ("failed" if output.get("error") else "success")
    return (
        status == "failed"
        and bool(output.get("error"))
        and output.get("confidence", 0.0) == 0.0
    )


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
        "fallback_used": state.get("fallback_used", False),
        "errors": list(state.get("errors", [])),
    }


def _tool_call_trace(result: dict[str, Any]) -> dict[str, Any]:
    rag_metadata = result.get("rag_metadata", {})
    gateway_metadata = result.get("gateway_metadata", {})
    return {
        "node": result.get("node", ""),
        "tool_name": result.get("tool_name", result.get("tool", "")),
        "status": result.get("status", "pending"),
        "tool_status": gateway_metadata.get("status", result.get("status", "pending")),
        "retry_count": result.get("retry_count", 0),
        "error": result.get("error", ""),
        "error_code": gateway_metadata.get("error_code", ""),
        "latency_ms": result.get("latency_ms", 0),
        "source": result.get("source", ""),
        "input_hash": gateway_metadata.get("input_hash", ""),
        "evidence_count": gateway_metadata.get("evidence_count", 0),
        "safe_summary": gateway_metadata.get("safe_summary", ""),
        "retrieval_top_k": rag_metadata.get("retrieval_top_k"),
        "score_threshold": rag_metadata.get("score_threshold"),
        "retrieved_count": rag_metadata.get("retrieved_count"),
        "grounding_status": rag_metadata.get("grounding_status", ""),
        "retrieval_latency_ms": rag_metadata.get("retrieval_latency_ms"),
        "retrieval_type": rag_metadata.get("retrieval_type", ""),
        "fallback_used": rag_metadata.get("fallback_used"),
        "embedding_provider": rag_metadata.get("embedding_provider", ""),
        "embedding_fallback_used": rag_metadata.get("embedding_fallback_used"),
        "rerank_provider": rag_metadata.get("rerank_provider", ""),
        "rerank_fallback_used": rag_metadata.get("rerank_fallback_used"),
    }


class _RAGRetrieverTool:
    name = "rag_retriever"

    def __init__(self):
        self._retriever = LocalKnowledgeRetriever()
        self._keyword_retriever = KeywordRetriever()

    def run(self, query: str) -> dict[str, Any]:
        retrieval = self._retriever.retrieve(query, top_k=5, score_threshold=0.12, retrieval_type="hybrid")
        keyword_retrieval = self._keyword_retriever.retrieve_with_evidence(query, top_k=5, retrieval_type="hybrid")
        documents = retrieval.get("documents", [])
        source = ",".join(dict.fromkeys(doc["source"] for doc in documents))
        if not documents and keyword_retrieval["retrieved_chunks"]:
            documents = [
                {
                    "content": chunk["content"],
                    "source": chunk["source"],
                    "title": chunk["title"],
                    "section": chunk["title"],
                    "chunk_id": chunk["chunk_id"],
                    "doc_type": chunk.get("doc_type", "markdown_doc"),
                    "line_range": chunk.get("line_range", [1, 1]),
                    "content_hash": chunk.get("content_hash", ""),
                    "score": chunk.get("score", 0.0),
                    "rerank_score": chunk.get("rerank_score", 0.0),
                    "match_reason": chunk.get("match_reason", ""),
                    "retrieval_type": "keyword",
                }
                for chunk in keyword_retrieval["retrieved_chunks"]
            ]
            source = ",".join(dict.fromkeys(str(doc["source"]) for doc in documents))
        evidence = [
            {
                "source": doc.get("source", ""),
                "title": doc.get("title", ""),
                "chunk_id": doc.get("chunk_id", ""),
                "line_range": doc.get("line_range", []),
                "content_excerpt": str(doc.get("content", ""))[:260],
                "score": doc.get("score", 0.0),
            }
            for doc in documents
        ]
        retrieved_chunks = keyword_retrieval["retrieved_chunks"] or [
            {
                "chunk_id": doc.get("chunk_id", ""),
                "source": doc.get("source", ""),
                "title": doc.get("title", ""),
                "content": doc.get("content", ""),
                "keywords": [],
                "doc_type": doc.get("doc_type", ""),
                "line_range": doc.get("line_range", []),
                "content_hash": doc.get("content_hash", ""),
                "rerank_score": doc.get("rerank_score", 0.0),
                "match_reason": doc.get("match_reason", ""),
                "score": doc.get("score", 0.0),
                "retrieval_type": doc.get("retrieval_type", "hybrid"),
            }
            for doc in documents
        ]
        rag_metadata = {
            "query": query,
            "rewritten_queries": keyword_retrieval.get("rewritten_queries", [query]),
            "query_expansions": keyword_retrieval.get("query_expansions", []),
            "retrieval_top_k": retrieval.get("retrieval_top_k", 5),
            "score_threshold": retrieval.get("score_threshold", 0.12),
            "retrieved_count": len(documents),
            "grounding_status": "grounded" if documents else keyword_retrieval["grounding_status"],
            "no_evidence_reason": "" if documents else keyword_retrieval["no_evidence_reason"],
            "retrieval_latency_ms": retrieval.get("retrieval_latency_ms", 0),
            "retrieval_type": keyword_retrieval.get("retrieval_type", retrieval.get("retrieval_type", "hybrid")),
            "keyword_hit_count": keyword_retrieval.get("keyword_hit_count", 0),
            "vector_hit_count": keyword_retrieval.get("vector_hit_count", 0),
            "fallback_used": retrieval.get("fallback_used", False),
            "vector_available": retrieval.get("vector_available", False),
            "rerank_applied": retrieval.get("rerank_applied", bool(keyword_retrieval.get("rerank_results"))),
            "dedup_count": retrieval.get("dedup_count", 0),
            "recall_at_k": retrieval.get("recall_at_k", 1.0 if documents else 0.0),
            "precision_at_k": retrieval.get("precision_at_k", round(len(documents) / 5, 4) if documents else 0.0),
            "source_coverage": retrieval.get("source_coverage", 0.0),
            "missing_source_count": retrieval.get("missing_source_count", 0),
            "grounded_answer_rate": retrieval.get("grounded_answer_rate", 1.0 if documents else 0.0),
            "embedding_provider": keyword_retrieval.get("embedding_provider", "local"),
            "embedding_model": keyword_retrieval.get("embedding_model", ""),
            "embedding_fallback_used": keyword_retrieval.get("embedding_fallback_used", False),
            "embedding_fallback_reason": keyword_retrieval.get("embedding_fallback_reason", ""),
            "rerank_provider": keyword_retrieval.get("rerank_provider", "local"),
            "rerank_model": keyword_retrieval.get("rerank_model", ""),
            "rerank_fallback_used": keyword_retrieval.get("rerank_fallback_used", False),
            "rerank_fallback_reason": keyword_retrieval.get("rerank_fallback_reason", ""),
            "retrieved_chunks": retrieved_chunks,
            "rerank_results": retrieval.get("rerank_results") or keyword_retrieval.get("rerank_results", []),
            "evidence": evidence,
        }

        if not documents and (error := retrieval.get("error")):
            return {
                "tool_name": self.name,
                "result": "知识库证据不足。" if error == "insufficient_evidence" else "知识库中未检索到直接相关内容。",
                "confidence": 0.0,
                "source": source or "data/docs",
                "documents": documents,
                "rag_metadata": rag_metadata,
                "error": error,
            }

        return {
            "tool_name": self.name,
            "result": f"检索到 {len(documents)} 条相关知识片段",
            "confidence": max((doc["score"] for doc in documents), default=0.0),
            "source": source,
            "documents": documents,
            "rag_metadata": rag_metadata,
        }
