"""Unified deterministic boundary for local tool execution."""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from app.tools.policies import ToolGatewayPolicy
from app.tools.registry import ToolRegistry, default_tool_registry
from app.tools.result import StandardToolResult


class ToolGateway:
    """Validate, execute, and normalize tool calls."""

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        policy: ToolGatewayPolicy | None = None,
    ) -> None:
        self.registry = registry or default_tool_registry()
        self.policy = policy or ToolGatewayPolicy()
        self._seen_hashes: set[str] = set()

    def execute(
        self,
        tool_name: str,
        params: dict[str, Any],
        tool: Any | None = None,
    ) -> StandardToolResult:
        input_hash = self._input_hash(tool_name, params)
        start = time.perf_counter()

        if not self.registry.is_registered(tool_name):
            return self._blocked(tool_name, input_hash, start, "tool_not_registered")

        validation_error = self.policy.validate_params(tool_name, params)
        if validation_error:
            return self._error(tool_name, input_hash, start, validation_error)

        if input_hash in self._seen_hashes:
            return self._blocked(tool_name, input_hash, start, "duplicate_call")
        self._seen_hashes.add(input_hash)

        if not self.policy.is_allowed(tool_name, params):
            return self._blocked(tool_name, input_hash, start, "tool_not_allowed")

        resolved_tool = tool or self.registry.create(tool_name)
        if resolved_tool is None:
            return self._error(tool_name, input_hash, start, "tool_not_bound")

        try:
            output = resolved_tool.run(str(params["query"]))
        except Exception as exc:
            return self._error(
                tool_name,
                input_hash,
                start,
                type(exc).__name__,
                metadata={"exception": str(exc)},
            )

        latency_ms = self._latency_ms(start)
        status = self._status_from_output(output)
        error_code = self._error_code_from_output(output, status)
        return StandardToolResult(
            tool_name=str(output.get("tool_name", tool_name)),
            status=status,
            latency_ms=latency_ms,
            input_hash=input_hash,
            evidence_count=self._evidence_count(output),
            safe_summary=self._safe_summary(output),
            error_code=error_code,
            metadata={"raw_output": output},
        )

    def _blocked(self, tool_name: str, input_hash: str, start: float, error_code: str) -> StandardToolResult:
        return StandardToolResult(
            tool_name=tool_name,
            status="blocked",
            latency_ms=self._latency_ms(start),
            input_hash=input_hash,
            evidence_count=0,
            safe_summary="",
            error_code=error_code,
            metadata={},
        )

    def _error(
        self,
        tool_name: str,
        input_hash: str,
        start: float,
        error_code: str,
        metadata: dict[str, Any] | None = None,
    ) -> StandardToolResult:
        return StandardToolResult(
            tool_name=tool_name,
            status="error",
            latency_ms=self._latency_ms(start),
            input_hash=input_hash,
            evidence_count=0,
            safe_summary="",
            error_code=error_code,
            metadata=metadata or {},
        )

    def _status_from_output(self, output: dict[str, Any]) -> str:
        raw_status = output.get("status", "")
        if raw_status == "partial_success":
            return "partial_success"
        if raw_status in {"failed", "error"} or output.get("error"):
            return "error"
        return "success"

    def _error_code_from_output(self, output: dict[str, Any], status: str) -> str:
        if status in {"success", "partial_success"}:
            return ""
        return str(output.get("error") or status)

    def _evidence_count(self, output: dict[str, Any]) -> int:
        documents = output.get("documents", []) or []
        rag_evidence = (output.get("rag_metadata", {}) or {}).get("evidence", []) or []
        if documents or rag_evidence:
            return len(documents) + len(rag_evidence)
        return 1 if output.get("result") else 0

    def _safe_summary(self, output: dict[str, Any]) -> str:
        result = str(output.get("result", "") or "")
        if result:
            return result[:300]
        error = str(output.get("error", "") or "")
        return error[:300]

    def _latency_ms(self, start: float) -> int:
        return int((time.perf_counter() - start) * 1000)

    def _input_hash(self, tool_name: str, params: dict[str, Any]) -> str:
        payload = json.dumps({"tool_name": tool_name, "params": params}, ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
