"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AppHeader } from "@/components/app-header";
import { EvaluationPanel } from "@/components/evaluation-panel";
import { TraceViewer } from "@/components/trace-viewer";
import {
  fetchRun,
  fetchRuns,
  type PersistedRunStep,
  type PersistedToolCall,
  type RunDetail,
  type RunSummary,
  type TraceData,
  type TraceSkippedNode,
  type TraceToolCall,
  type ToolResult,
} from "@/lib/api";

function asRecord(value: unknown): Record<string, unknown> {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return {};
}

function asArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatScore(value?: number | null) {
  if (typeof value !== "number") return "-";
  return `${Math.round(value * 100)}%`;
}

function formatLatency(value?: number | null) {
  if (typeof value !== "number") return "-";
  return `${Math.round(value)}ms`;
}

function routeLabel(route?: string | null) {
  if (route === "simple_qa") return "简单问答";
  if (route === "complex_troubleshooting") return "复杂排障";
  return route || "-";
}

function statusClass(status?: string | null) {
  if (status === "success") return "badge-green";
  if (status === "failed" || status === "error") return "rounded-full bg-red-50 px-2.5 py-0.5 text-xs font-medium text-red-700";
  return "badge-slate";
}

function stepToTraceToolCall(call: unknown): TraceToolCall {
  const data = asRecord(call);
  return {
    node: String(data.node ?? ""),
    tool_name: String(data.tool_name ?? data.tool ?? ""),
    status: String(data.status ?? ""),
    retry_count: Number(data.retry_count ?? 0),
    error: typeof data.error === "string" ? data.error : undefined,
    latency_ms: typeof data.latency_ms === "number" ? data.latency_ms : undefined,
    source: typeof data.source === "string" ? data.source : undefined,
  };
}

function persistedToolCallToTrace(call: PersistedToolCall): TraceToolCall {
  return {
    node: call.node ?? undefined,
    tool_name: call.tool_name ?? undefined,
    status: call.status ?? undefined,
    retry_count: call.retry_count ?? 0,
    error: call.error ?? undefined,
    latency_ms: call.latency_ms ?? undefined,
    source: call.source ?? undefined,
  };
}

function buildTrace(detail: RunDetail | null): TraceData | undefined {
  if (!detail) return undefined;
  const persistedCalls = detail.tool_calls.map(persistedToolCallToTrace);
  return {
    trace_id: detail.run.run_id,
    steps: detail.steps.map((step) => {
      const output = asRecord(step.output);
      const toolCalls = asArray<unknown>(output.tool_calls).map(stepToTraceToolCall);
      const skippedNodes = asArray<TraceSkippedNode>(output.skipped_nodes);

      return {
        stage: step.stage,
        engine: step.engine ?? undefined,
        graph_name: typeof output.graph_name === "string" ? output.graph_name : undefined,
        output: typeof output.output === "string" ? output.output : JSON.stringify(output),
        latency_ms: step.latency_ms ?? undefined,
        llm_used: typeof output.llm_used === "boolean" ? output.llm_used : undefined,
        llm_error: typeof output.llm_error === "string" ? output.llm_error : null,
        prompt_version: typeof output.prompt_version === "string" ? output.prompt_version : undefined,
        tool_calls: step.stage === "executor" ? (toolCalls.length > 0 ? toolCalls : persistedCalls) : toolCalls,
        skipped_nodes: skippedNodes,
        fallback_used: typeof output.fallback_used === "boolean" ? output.fallback_used : undefined,
        overall_score: typeof output.overall_score === "number" ? output.overall_score : null,
        evaluation_error: typeof output.evaluation_error === "string" ? output.evaluation_error : null,
      };
    }),
  };
}

function buildToolResults(detail: RunDetail | null): ToolResult[] {
  if (!detail) return [];
  return detail.tool_calls.map((call) => {
    const result = asRecord(call.result);
    return {
      tool_name: call.tool_name ?? undefined,
      tool: call.tool_name ?? undefined,
      status: call.status || "unknown",
      confidence: call.confidence ?? 0,
      source: call.source || "local",
      result: typeof result.result === "string" ? result.result : JSON.stringify(result),
      latency_ms: call.latency_ms ?? undefined,
    };
  });
}

function findPersistedAnswer(detail: RunDetail | null) {
  const evaluationStep = detail?.steps.find((step) => step.stage === "evaluation");
  const input = asRecord(evaluationStep?.input);
  return typeof input.answer === "string" ? input.answer : "";
}

function RunListItem({
  run,
  selected,
  onSelect,
}: {
  run: RunSummary;
  selected: boolean;
  onSelect: (runId: string) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onSelect(run.run_id)}
      className={`w-full rounded-xl border px-4 py-3 text-left transition-colors ${
        selected
          ? "border-emerald-300 bg-emerald-50/60"
          : "border-slate-200 bg-white hover:border-slate-300"
      }`}
    >
      <div className="flex items-center justify-between gap-3">
        <span className="truncate text-sm font-semibold text-slate-900">{run.query}</span>
        <span className="shrink-0 text-xs text-slate-400">{formatDate(run.created_at)}</span>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <span className="badge-blue">{routeLabel(run.route_type)}</span>
        <span className={statusClass(run.status)}>{run.status || "unknown"}</span>
        <span className="badge-slate">{formatLatency(run.total_latency_ms)}</span>
        <span className="badge-green">评分 {formatScore(run.evaluation_score)}</span>
      </div>
    </button>
  );
}

function ToolCallTable({ toolCalls }: { toolCalls: PersistedToolCall[] }) {
  if (toolCalls.length === 0) {
    return <p className="text-sm text-slate-400">暂无工具调用。</p>;
  }

  return (
    <div className="overflow-hidden rounded-xl border border-slate-100">
      <table className="min-w-full divide-y divide-slate-100 text-sm">
        <thead className="bg-slate-50 text-xs text-slate-500">
          <tr>
            <th className="px-3 py-2 text-left font-medium">工具</th>
            <th className="px-3 py-2 text-left font-medium">节点</th>
            <th className="px-3 py-2 text-left font-medium">状态</th>
            <th className="px-3 py-2 text-left font-medium">耗时</th>
            <th className="px-3 py-2 text-left font-medium">置信度</th>
            <th className="px-3 py-2 text-left font-medium">结果摘要</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {toolCalls.map((call, index) => {
            const result = asRecord(call.result);
            const summary = typeof result.result === "string" ? result.result : JSON.stringify(result);
            return (
              <tr key={`${call.tool_name}-${index}`} className="align-top">
                <td className="px-3 py-2 font-medium text-slate-800">{call.tool_name || "-"}</td>
                <td className="px-3 py-2 text-slate-500">{call.node || "-"}</td>
                <td className="px-3 py-2 text-slate-500">{call.status || "-"}</td>
                <td className="px-3 py-2 text-slate-500">{formatLatency(call.latency_ms)}</td>
                <td className="px-3 py-2 text-slate-500">{formatScore(call.confidence)}</td>
                <td className="max-w-md px-3 py-2 text-slate-600">
                  <span className="line-clamp-2">{summary || "-"}</span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default function RunsPage() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selectedRunId, setSelectedRunId] = useState("");
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [isLoadingRuns, setIsLoadingRuns] = useState(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    setIsLoadingRuns(true);
    fetchRuns(50)
      .then((data) => {
        if (!mounted) return;
        setRuns(data);
        if (data.length > 0) setSelectedRunId(data[0].run_id);
      })
      .catch(() => {
        if (mounted) setError("历史记录加载失败，请确认后端服务是否已启动。");
      })
      .finally(() => {
        if (mounted) setIsLoadingRuns(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedRunId) {
      setDetail(null);
      return;
    }

    let mounted = true;
    setIsLoadingDetail(true);
    fetchRun(selectedRunId)
      .then((data) => {
        if (mounted) setDetail(data);
      })
      .catch(() => {
        if (mounted) setError("Run 明细加载失败。");
      })
      .finally(() => {
        if (mounted) setIsLoadingDetail(false);
      });

    return () => {
      mounted = false;
    };
  }, [selectedRunId]);

  const trace = useMemo(() => buildTrace(detail), [detail]);
  const toolResults = useMemo(() => buildToolResults(detail), [detail]);
  const answer = findPersistedAnswer(detail);
  const selectedRun = detail?.run ?? runs.find((run) => run.run_id === selectedRunId);

  return (
    <main className="min-h-screen bg-slate-50">
      <AppHeader evaluation={detail?.evaluation} trace={trace} toolResults={toolResults} />

      <div className="mx-auto max-w-7xl px-6 py-6 lg:px-8">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">历史执行记录</h2>
            <p className="text-sm text-slate-500">查看历史问题、路由结果、工具调用、执行耗时和质量评分。</p>
          </div>
          <Link
            href="/"
            className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:border-emerald-300 hover:text-emerald-700"
          >
            返回实时排障
          </Link>
        </div>

        {error && (
          <div className="mb-4 rounded-xl border border-red-200 bg-red-50/50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-[380px_minmax(0,1fr)]">
          <section className="card h-fit">
            <div className="card-header flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-900">最近 Runs</h3>
              <span className="badge-slate">{runs.length} 条</span>
            </div>
            <div className="card-body space-y-3">
              {isLoadingRuns && <p className="text-sm text-slate-400">正在加载历史记录...</p>}
              {!isLoadingRuns && runs.length === 0 && <p className="text-sm text-slate-400">暂无历史 Run。</p>}
              {runs.map((run) => (
                <RunListItem
                  key={run.run_id}
                  run={run}
                  selected={run.run_id === selectedRunId}
                  onSelect={setSelectedRunId}
                />
              ))}
            </div>
          </section>

          <section className="min-w-0 space-y-4">
            {isLoadingDetail && (
              <div className="card">
                <div className="card-body text-sm text-slate-400">正在加载 Run 明细...</div>
              </div>
            )}

            {!isLoadingDetail && selectedRun && (
              <>
                <div className="card">
                  <div className="card-header">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="min-w-0">
                        <h3 className="truncate text-sm font-semibold text-slate-900">{selectedRun.query}</h3>
                        <p className="mt-1 text-xs text-slate-400">Run ID: {selectedRun.run_id}</p>
                      </div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="badge-blue">{routeLabel(selectedRun.route_type)}</span>
                        <span className={statusClass(selectedRun.status)}>{selectedRun.status || "unknown"}</span>
                        <span className="badge-slate">{selectedRun.answer_source || "fallback"}</span>
                      </div>
                    </div>
                  </div>
                  <div className="card-body grid gap-3 sm:grid-cols-4">
                    <div className="rounded-lg border border-slate-100 bg-slate-50/50 p-3">
                      <p className="text-xs text-slate-400">创建时间</p>
                      <p className="mt-1 text-sm font-semibold text-slate-800">{formatDate(selectedRun.created_at)}</p>
                    </div>
                    <div className="rounded-lg border border-slate-100 bg-slate-50/50 p-3">
                      <p className="text-xs text-slate-400">总耗时</p>
                      <p className="mt-1 text-sm font-semibold text-slate-800">{formatLatency(selectedRun.total_latency_ms)}</p>
                    </div>
                    <div className="rounded-lg border border-slate-100 bg-slate-50/50 p-3">
                      <p className="text-xs text-slate-400">工具调用</p>
                      <p className="mt-1 text-sm font-semibold text-slate-800">{detail?.tool_calls.length ?? 0}</p>
                    </div>
                    <div className="rounded-lg border border-slate-100 bg-slate-50/50 p-3">
                      <p className="text-xs text-slate-400">质量评分</p>
                      <p className="mt-1 text-sm font-semibold text-slate-800">{formatScore(selectedRun.evaluation_score)}</p>
                    </div>
                  </div>
                </div>

                {answer && (
                  <div className="card">
                    <div className="card-header">
                      <h3 className="text-sm font-semibold text-slate-900">历史回答</h3>
                    </div>
                    <div className="card-body">
                      <p className="whitespace-pre-wrap text-sm leading-7 text-slate-800">{answer}</p>
                    </div>
                  </div>
                )}

                <div className="card">
                  <div className="card-header">
                    <h3 className="text-sm font-semibold text-slate-900">工具调用回放</h3>
                  </div>
                  <div className="card-body">
                    <ToolCallTable toolCalls={detail?.tool_calls ?? []} />
                  </div>
                </div>

                <TraceViewer trace={trace} routeType={selectedRun.route_type || undefined} />
                <EvaluationPanel evaluation={detail?.evaluation} />
              </>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
