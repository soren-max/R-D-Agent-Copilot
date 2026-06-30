from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.evidence.confidence import candidate_confidence, clamp_confidence, evidence_confidence, overall_confidence
from app.evidence.schemas import EvidenceChain, EvidenceItem, RootCauseCandidate


TOOL_TYPE_MAP = {
    "log_tool": "log",
    "config_tool": "config",
    "git_tool": "git",
    "rag_retriever": "rag",
}

TYPE_LABELS = {
    "log": "日志",
    "config": "配置",
    "git": "Git",
    "rag": "知识库",
    "evaluation": "评估",
}


class EvidenceChainBuilder:
    """Builds deterministic evidence and confidence from existing agent outputs."""

    def build(self, payload: dict[str, Any] | BaseModel) -> EvidenceChain:
        data = self._as_dict(payload)
        tool_results = [self._as_dict(result) for result in data.get("tool_results", [])]
        evaluation = self._as_dict(data.get("evaluation", {}))

        evidence_items = self._build_tool_evidence(tool_results)
        evaluation_item = self._build_evaluation_evidence(evaluation)
        if evaluation_item is not None:
            evidence_items.append(evaluation_item)

        failed_tool_count = sum(
            1
            for result in tool_results
            if result.get("tool") != "none" and result.get("status") == "failed"
        )
        evaluation_score = self._evaluation_score(evaluation)
        candidates = self._build_root_cause_candidates(
            data=data,
            evidence_items=evidence_items,
            failed_tool_count=failed_tool_count,
            evaluation_score=evaluation_score,
        )

        success_rate = self._tool_success_rate(tool_results)
        return EvidenceChain(
            overall_confidence=overall_confidence(
                candidates,
                evidence_items,
                tool_success_rate=success_rate,
                evaluation_score=evaluation_score,
            ),
            root_cause_candidates=candidates,
            evidence_items=evidence_items,
        )

    def _build_tool_evidence(self, tool_results: list[dict[str, Any]]) -> list[EvidenceItem]:
        counters: dict[str, int] = {}
        evidence_items: list[EvidenceItem] = []
        for result in tool_results:
            tool_name = result.get("tool_name") or result.get("tool", "")
            evidence_type = TOOL_TYPE_MAP.get(tool_name)
            if evidence_type is None:
                continue

            counters[evidence_type] = counters.get(evidence_type, 0) + 1
            evidence_id = f"ev_{evidence_type}_{counters[evidence_type]:03d}"
            evidence_items.append(
                EvidenceItem(
                    id=evidence_id,
                    type=evidence_type,
                    source=result.get("source", ""),
                    summary=self._summarize_tool_result(evidence_type, result),
                    confidence=evidence_confidence(result),
                    related_tool=tool_name,
                )
            )
        return evidence_items

    def _build_evaluation_evidence(self, evaluation: dict[str, Any]) -> EvidenceItem | None:
        if not evaluation:
            return None
        overall_score = self._evaluation_score(evaluation)
        if overall_score is None:
            return None

        issues = evaluation.get("issues") or []
        issue_text = "；".join(str(issue) for issue in issues[:2])
        summary = f"Evaluation overall_score={overall_score:.2f}"
        if issue_text:
            summary = f"{summary}，主要问题：{issue_text}"

        return EvidenceItem(
            id="ev_evaluation_001",
            type="evaluation",
            source="rule_based_evaluator",
            summary=summary,
            confidence=clamp_confidence(overall_score),
            related_tool="evaluation",
        )

    def _build_root_cause_candidates(
        self,
        data: dict[str, Any],
        evidence_items: list[EvidenceItem],
        failed_tool_count: int,
        evaluation_score: float | None,
    ) -> list[RootCauseCandidate]:
        route = self._as_dict(data.get("route", {}))
        if route.get("type") != "complex_troubleshooting":
            return []

        by_type = {item.type: item for item in evidence_items}
        evidence_types = set(by_type.keys())
        supporting_types = [item_type for item_type in ["log", "config", "git", "rag"] if item_type in by_type]
        supporting_ids = [by_type[item_type].id for item_type in supporting_types]
        if not supporting_ids:
            return []

        if {"log", "config"}.issubset(evidence_types):
            title = "日志异常与配置差异共同指向服务超时风险"
            reason = "日志证据显示请求异常或超时，同时配置证据显示环境配置存在差异，二者共同支持该根因方向。"
        elif {"log", "git"}.issubset(evidence_types):
            title = "日志异常可能与近期代码变更相关"
            reason = "日志证据显示运行时异常，Git 证据提供了相关变更线索，建议优先核对变更影响面。"
        elif "config" in evidence_types:
            title = "配置差异可能导致当前故障现象"
            reason = "配置证据提供了环境差异线索，但仍需要结合日志或变更记录进一步确认。"
        elif "log" in evidence_types:
            title = "日志异常提示服务运行时故障"
            reason = "日志证据提供了直接故障现象，但缺少配置或代码变更的交叉验证。"
        elif "git" in evidence_types:
            title = "近期代码变更可能影响服务行为"
            reason = "Git 证据提供了变更线索，但缺少日志或配置证据的交叉验证。"
        else:
            title = "知识库证据提供了排查方向"
            reason = "知识库检索结果可作为补充背景，但不能单独确认根因。"

        return [
            RootCauseCandidate(
                title=title,
                confidence=candidate_confidence(evidence_types, failed_tool_count, evaluation_score),
                supporting_evidence_ids=supporting_ids,
                reason=reason,
            )
        ]

    def _summarize_tool_result(self, evidence_type: str, result: dict[str, Any]) -> str:
        status = result.get("status", "success")
        if status == "failed" or result.get("error"):
            return f"{TYPE_LABELS[evidence_type]}工具执行失败：{result.get('error') or 'unknown_error'}"

        if evidence_type == "rag":
            documents = result.get("documents") or []
            if documents:
                sources = ",".join(dict.fromkeys(str(doc.get("source", "")) for doc in documents if doc.get("source")))
                return f"知识库检索到 {len(documents)} 条相关片段，来源：{sources or result.get('source', 'data/docs')}"

        text = str(result.get("result") or "").strip()
        if not text:
            return f"{TYPE_LABELS[evidence_type]}工具返回成功，但没有可展示摘要。"
        return text if len(text) <= 160 else f"{text[:157]}..."

    def _tool_success_rate(self, tool_results: list[dict[str, Any]]) -> float:
        executed = [
            result
            for result in tool_results
            if result.get("tool") != "none" and result.get("status") != "skipped"
        ]
        if not executed:
            return 0.0
        success_count = sum(1 for result in executed if result.get("status") == "success")
        return clamp_confidence(success_count / len(executed), default=0.0)

    def _evaluation_score(self, evaluation: dict[str, Any]) -> float | None:
        if not evaluation:
            return None
        value = evaluation.get("overall_score")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return clamp_confidence(value)

    def _as_dict(self, value: Any) -> dict[str, Any]:
        if isinstance(value, BaseModel):
            return value.model_dump()
        if isinstance(value, dict):
            return value
        return {}
