"use client";

import { useState } from "react";
import type { TraceStep } from "@/lib/api";
import { StatusBadge } from "@/components/shared/status-badge";
import { JsonViewer } from "@/components/shared/json-viewer";

type TraceStepCardProps = {
  step: TraceStep;
  index: number;
};

const stageOrder = ["router", "planner", "executor", "synthesizer", "evaluation"];

const stageColors: Record<string, string> = {
  router: "#6366f1",
  planner: "#0284c7",
  executor: "#d97706",
  synthesizer: "#8b5cf6",
  evaluation: "#059669",
};

const stageIcons: Record<string, string> = {
  router: "▶",
  planner: "◎",
  executor: "⚙",
  synthesizer: "◆",
  evaluation: "◉",
};

function stageLabel(stage?: string): string {
  const map: Record<string, string> = {
    router: "Router 路由器",
    planner: "Planner 任务规划",
    executor: "LangGraph Executor 执行器",
    synthesizer: "Answer Synthesizer 回答生成",
    evaluation: "Evaluation 质量评估",
  };
  return map[stage ?? ""] || stage || "Unknown";
}

function formatLatency(ms?: number): string {
  if (ms == null) return "-";
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`;
}

function truncate(str?: string, max = 120): string {
  if (!str) return "—";
  return str.length > max ? str.slice(0, max) + "…" : str;
}

function getOutputSummary(step: TraceStep): string {
  return step.output || "";
}

function getInputSummary(step: TraceStep): string {
  if (step.stage === "router") return "用户输入 → 意图分类";
  if (step.stage === "planner") return "Router 结果 → 执行步骤";
  if (step.stage === "executor") return `执行 ${step.tool_calls?.length ?? 0} 个工具`;
  if (step.stage === "synthesizer") return `LLM: ${step.llm_used ? "是" : "否"}`;
  if (step.stage === "evaluation") return "质量评估";
  return "-";
}

export function TraceStepCard({ step, index }: TraceStepCardProps) {
  const [expanded, setExpanded] = useState(index === 0);
  const status = step.llm_error ? "error" : step.fallback_used ? "warning" : "success";
  const color = stageColors[step.stage ?? ""] || "#64748b";
  const icon = stageIcons[step.stage ?? ""] || "●";

  return (
    <div className="relative">
      {/* Connector line */}
      {index > 0 && (
        <div className="absolute left-[19px] top-0 h-4 w-0.5" style={{ background: "var(--border)" }} />
      )}

      <div className="relative flex gap-4 pb-6 last:pb-0">
        {/* Stage icon */}
        <div className="relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-sm font-bold text-white" style={{ background: color }}>
          {icon}
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1">
          <div
            className="cursor-pointer rounded-xl border px-4 py-3 transition-all hover:shadow-sm"
            style={{ borderColor: "var(--border)", background: "var(--bg-card)" }}
            onClick={() => setExpanded(!expanded)}
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                  {stageLabel(step.stage)}
                </span>
                <StatusBadge status={status} />
              </div>
              <div className="flex items-center gap-2 text-xs" style={{ color: "var(--text-tertiary)" }}>
                <span>{formatLatency(step.latency_ms)}</span>
                {step.engine && (
                  <span className="rounded-md px-2 py-0.5 font-medium" style={{ background: "var(--accent-light)", color: "var(--accent)" }}>
                    {step.engine}
                  </span>
                )}
                <span className="text-xs">{expanded ? "▲" : "▼"}</span>
              </div>
            </div>

            {/* Summary always visible */}
            <div className="mt-2 grid gap-x-6 gap-y-1 text-xs sm:grid-cols-2" style={{ color: "var(--text-tertiary)" }}>
              <div className="truncate">
                <span className="font-medium" style={{ color: "var(--text-secondary)" }}>输入：</span>
                {getInputSummary(step)}
              </div>
              <div className="truncate">
                <span className="font-medium" style={{ color: "var(--text-secondary)" }}>输出：</span>
                {truncate(getOutputSummary(step))}
              </div>
            </div>

            {/* Expanded detail */}
            {expanded && (
              <div className="mt-3 space-y-3 border-t pt-3" style={{ borderColor: "var(--border-light)" }}>
                {/* Tool calls */}
                {step.tool_calls && step.tool_calls.length > 0 && (
                  <div>
                    <p className="mb-1.5 text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>
                      工具调用 ({step.tool_calls.length})
                    </p>
                    <div className="space-y-1">
                      {step.tool_calls.map((tc, i) => (
                        <div key={i} className="flex flex-wrap items-center gap-2 rounded-lg px-3 py-2 text-xs" style={{ background: "var(--bg-subtle)" }}>
                          <StatusBadge status={tc.status || "pending"} />
                          <span className="font-medium" style={{ color: "var(--text-primary)" }}>{tc.tool_name || tc.node || "未知工具"}</span>
                          {tc.latency_ms != null && <span style={{ color: "var(--text-tertiary)" }}>{formatLatency(tc.latency_ms)}</span>}
                          {tc.retry_count != null && tc.retry_count > 0 && <span className="badge-warning">重试 {tc.retry_count}</span>}
                          {tc.error && <span style={{ color: "var(--error)" }}>错误: {tc.error}</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Skipped nodes */}
                {step.skipped_nodes && step.skipped_nodes.length > 0 && (
                  <div>
                    <p className="mb-1.5 text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>
                      跳过节点 ({step.skipped_nodes.length})
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {step.skipped_nodes.map((sn, i) => (
                        <span key={i} className="rounded-md px-2 py-1 text-xs" style={{ background: "var(--bg-subtle)", color: "var(--text-tertiary)" }}>
                          {sn.node || sn.tool_name} {sn.reason ? `(${sn.reason})` : ""}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Full output */}
                {step.output && (
                  <div>
                    <p className="mb-1 text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>阶段输出</p>
                    <p className="rounded-lg px-3 py-2 text-xs leading-5" style={{ background: "var(--bg-subtle)", color: "var(--text-secondary)" }}>
                      {step.output}
                    </p>
                  </div>
                )}

                {/* Raw JSON */}
                <JsonViewer data={step} collapsed />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
