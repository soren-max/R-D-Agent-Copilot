"""Build layered ContextPackage objects for final answer generation."""

from __future__ import annotations

import json
from typing import Any

from app.memory.memory_store import MemoryStore
from apps.api.app.context.reducers import (
    reduce_rag_evidence,
    reduce_run_history,
    reduce_tool_evidence,
    summarize_text,
    stable_json,
)
from apps.api.app.context.metadata import ContextMetadata
from apps.api.app.context.sections import ContextPackage, ContextSection

SYSTEM_PREFIX = (
    "你是 R&D Agent Copilot 的最终 Answer Synthesizer。只能基于 Router、Planner、"
    "Executor 工具结果、RAG evidence 和 trace 摘要生成中文回答；不得编造外部事实。"
)


class ContextManager:
    """Create budgeted, layered context for the Answer Synthesizer."""

    def __init__(
        self,
        tool_budget: int = 2400,
        rag_budget: int = 2200,
        history_budget: int = 1800,
        memory_budget: int = 900,
        total_budget: int = 7200,
        memory_store: MemoryStore | None = None,
    ) -> None:
        self.tool_budget = tool_budget
        self.rag_budget = rag_budget
        self.history_budget = history_budget
        self.memory_budget = memory_budget
        self.total_budget = total_budget
        self.memory_store = memory_store or MemoryStore()

    def build(
        self,
        query: str,
        route: dict[str, Any],
        plan: dict[str, Any],
        tool_results: list[dict[str, Any]] | None = None,
        trace_summary: dict[str, Any] | None = None,
    ) -> ContextPackage:
        return self.build_context_package(query, route, plan, tool_results, trace_summary)

    def build_context_package(
        self,
        query: str,
        route: dict[str, Any],
        plan: dict[str, Any],
        tool_results: list[dict[str, Any]] | None = None,
        trace_summary: dict[str, Any] | None = None,
    ) -> ContextPackage:
        tool_results = tool_results or []
        trace_summary = trace_summary or {}

        raw_tool = self._build_tool_evidence(tool_results)
        tool_evidence, tool_reduced = reduce_tool_evidence(tool_results, self.tool_budget)
        raw_rag = self._build_rag_evidence(tool_results)
        rag_evidence, rag_reduced = reduce_rag_evidence(tool_results, self.rag_budget)
        raw_history = stable_json(trace_summary)
        run_history, history_reduced = reduce_run_history(trace_summary, self.history_budget)
        route_plan = stable_json({"route": route, "plan": plan})
        raw_memory, incident_memory, memory_reduced = self._build_incident_memory(query)

        sections = [
            self._section("system_prefix", SYSTEM_PREFIX, SYSTEM_PREFIX),
            self._section("current_query", query, query),
            self._section("route_plan", route_plan, route_plan),
            self._section("tool_evidence", raw_tool, tool_evidence, tool_reduced),
            self._section("rag_evidence", raw_rag, rag_evidence, rag_reduced),
            self._section("incident_memory", raw_memory, incident_memory, memory_reduced),
            self._section("run_history", raw_history, run_history, history_reduced),
        ]
        sections = self._apply_total_budget(sections)
        return ContextPackage(sections=sections, metadata=self._metadata(sections))

    def _section(self, name: str, before: str, after: str, reduced: bool = False) -> ContextSection:
        return ContextSection(
            name=name,
            content=after,
            chars_before=len(before),
            chars_after=len(after),
            reduced=reduced or len(after) < len(before),
        )

    def _build_tool_evidence(self, tool_results: list[dict[str, Any]]) -> str:
        items: list[dict[str, Any]] = []
        for result in tool_results:
            tool = result.get("tool") or result.get("tool_name", "")
            if tool == "rag_retriever":
                continue
            items.append({
                "tool": tool,
                "status": result.get("status", ""),
                "source": result.get("source", ""),
                "confidence": result.get("confidence", 0),
                "error": result.get("error", ""),
                "result": result.get("result", ""),
            })
        return stable_json(items)

    def _build_rag_evidence(self, tool_results: list[dict[str, Any]]) -> str:
        rag_results = [
            result for result in tool_results
            if result.get("tool") == "rag_retriever" or result.get("tool_name") == "rag_retriever"
        ]
        payload = []
        for result in rag_results:
            payload.append({
                "status": result.get("status", ""),
                "error": result.get("error", ""),
                "documents": result.get("documents", []),
                "rag_metadata": result.get("rag_metadata", {}),
            })
        return stable_json(payload)

    def _build_incident_memory(self, query: str) -> tuple[str, str, bool]:
        service = self._infer_service_from_query(query)
        results = self.memory_store.query_by_service_or_symptom(query=query, service=service, limit=3)
        payload = [
            {
                **result.to_context_dict(),
                "notice": "历史参考，不是当前工具证据；必须由当前 tool_evidence 或 rag_evidence 支撑后才能作为根因。",
            }
            for result in results
        ]
        raw = stable_json(payload)
        reduced, did_reduce = summarize_text(raw, self.memory_budget, "incident_memory")
        return raw, reduced, did_reduce

    def _apply_total_budget(self, sections: list[ContextSection]) -> list[ContextSection]:
        """Apply default trimming order without ever trimming current_query."""

        if self.total_budget <= 0:
            return sections
        by_name = {section.name: section for section in sections}
        trim_order = ["run_history", "incident_memory", "rag_evidence", "tool_evidence", "route_plan", "system_prefix"]
        current_total = sum(section.chars_after for section in sections)
        for name in trim_order:
            if current_total <= self.total_budget:
                break
            section = by_name.get(name)
            if section is None or not section.content:
                continue
            overflow = current_total - self.total_budget
            next_budget = max(120, section.chars_after - overflow)
            if next_budget >= section.chars_after:
                continue
            content, reduced = summarize_text(section.content, next_budget, name)
            current_total -= section.chars_after - len(content)
            section.content = content
            section.chars_after = len(content)
            section.reduced = section.reduced or reduced
        return sections

    def _metadata(self, sections: list[ContextSection]) -> ContextMetadata:
        total_before = sum(section.chars_before for section in sections)
        total_after = sum(section.chars_after for section in sections)
        ratio = 1.0 if total_before == 0 else round(total_after / total_before, 4)
        incident_memory = next((section for section in sections if section.name == "incident_memory"), None)
        memory_items = self._memory_items(incident_memory.content if incident_memory else "[]")
        return ContextMetadata(
            total_chars_before=total_before,
            total_chars_after=total_after,
            compression_ratio=ratio,
            section_char_counts={section.name: section.chars_after for section in sections},
            reduced_sections=[section.name for section in sections if section.reduced],
            memory_hit_count=len(memory_items),
            fresh_memory_count=sum(1 for item in memory_items if item.get("freshness_status") == "fresh"),
            stale_memory_count=sum(1 for item in memory_items if item.get("freshness_status") == "stale"),
        )

    def _memory_items(self, content: str) -> list[dict[str, Any]]:
        try:
            parsed = json.loads(content)
        except Exception:
            return []
        return parsed if isinstance(parsed, list) else []

    def _infer_service_from_query(self, query: str) -> str | None:
        import re

        service_match = re.search(r"([A-Za-z0-9_-]+-service)", query)
        if service_match:
            return service_match.group(1)
        if "订单" in query:
            return "order-service"
        return None


def build_context_package(
    query: str,
    route: dict[str, Any],
    plan: dict[str, Any],
    tool_results: list[dict[str, Any]] | None = None,
    trace_summary: dict[str, Any] | None = None,
) -> ContextPackage:
    """Compatibility function; prefer ContextManager().build(...)."""

    return ContextManager().build(query, route, plan, tool_results, trace_summary)
