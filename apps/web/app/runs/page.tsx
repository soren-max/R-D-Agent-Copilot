"use client";

import { useEffect, useMemo, useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { TraceStepCard } from "@/components/trace/trace-step-card";
import { MetricCard } from "@/components/shared/metric-card";
import { StatusBadge } from "@/components/shared/status-badge";
import { LoadingState } from "@/components/shared/loading-state";
import { ErrorState } from "@/components/shared/error-state";
import { EmptyState } from "@/components/shared/empty-state";
import { fetchRun, fetchRuns, type RunDetail, type RunSummary, type TraceStep } from "@/lib/api";
import { mockTraceData } from "@/lib/mock/trace";

function formatDate(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }).format(date);
}

function formatScore(value?: number | null) {
  if (typeof value !== "number") return "-";
  return `${Math.round(value * 100)}%`;
}

function formatLatency(value?: number | null) {
  if (typeof value !== "number") return "-";
  return value >= 1000 ? `${(value / 1000).toFixed(1)}s` : `${value}ms`;
}

function routeLabel(route?: string | null) {
  if (route === "simple_qa") return "简单问答";
  if (route === "complex_troubleshooting") return "复杂排障";
  return route || "-";
}

function RunListItem({ run, selected, onSelect }: { run: RunSummary; selected: boolean; onSelect: (id: string) => void }) {
  return (
    <button type="button" onClick={() => onSelect(run.run_id)}
      className={`w-full rounded-xl border px-4 py-3 text-left transition-colors ${
        selected ? "border-indigo-300 bg-indigo-50/60 dark:border-indigo-700 dark:bg-indigo-950/30" : "border-slate-200 hover:border-slate-300 dark:border-slate-700 dark:hover:border-slate-600"
      }`}
      style={{ background: selected ? undefined : "var(--bg-card)" }}
    >
      <div className="flex items-center justify-between gap-3">
        <span className="truncate text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{run.query}</span>
        <span className="shrink-0 text-xs" style={{ color: "var(--text-tertiary)" }}>{formatDate(run.created_at)}</span>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        <StatusBadge status={run.route_type === "complex_troubleshooting" ? "success" : "pending"} label={routeLabel(run.route_type)} />
        <StatusBadge status={run.status === "success" ? "success" : run.status === "failed" ? "error" : "pending"} label={run.status || "unknown"} />
        <span className="rounded-md px-2 py-0.5 text-xs" style={{ background: "var(--bg-subtle)", color: "var(--text-tertiary)" }}>{formatLatency(run.total_latency_ms)}</span>
      </div>
    </button>
  );
}

export default function RunsPage() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selectedRunId, setSelectedRunId] = useState("");
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [isLoadingRuns, setIsLoadingRuns] = useState(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [useMock, setUseMock] = useState(false);

  // Load runs list
  useEffect(() => {
    let mounted = true;
    setIsLoadingRuns(true);
    fetchRuns(50)
      .then((data) => {
        if (!mounted) return;
        if (data.length === 0) { setUseMock(true); return; }
        setRuns(data);
      })
      .catch(() => { if (mounted) setUseMock(true); })
      .finally(() => { if (mounted) setIsLoadingRuns(false); });
    return () => { mounted = false; };
  }, []);

  // Load run detail when a run is selected
  useEffect(() => {
    if (!selectedRunId) { setDetail(null); setDetailError(null); return; }
    let mounted = true;
    setIsLoadingDetail(true);
    setDetailError(null);
    fetchRun(selectedRunId)
      .then((data) => {
        if (mounted) setDetail(data);
      })
      .catch(() => {
        if (mounted) {
          setDetail(null);
          setDetailError("Run 详情加载失败，请检查后端 /runs/{run_id} 接口。");
        }
      })
      .finally(() => { if (mounted) setIsLoadingDetail(false); });
    return () => { mounted = false; };
  }, [selectedRunId]);

  // Build trace data from either mock or real RunDetail
  const traceData = useMock ? mockTraceData : buildTraceFromDetail(detail);
  const steps = traceData?.steps ?? [];
  const selectedRun = runs.find((r) => r.run_id === selectedRunId);
  const hasDetail = detail !== null && !isLoadingDetail && !detailError;

  // Build a TraceData-compatible object from RunDetail
  function buildTraceFromDetail(d: RunDetail | null): typeof mockTraceData | null {
    if (!d || !d.run) return null;
    return {
      trace_id: d.run.run_id,
      steps: (d.steps || []).map((step: any) => ({
        stage: step.stage,
        engine: step.engine || undefined,
        output: typeof step.output === "object" ? JSON.stringify(step.output) : (step.output || ""),
        latency_ms: step.latency_ms ?? 0,
        llm_used: typeof step.output?.llm_used === "boolean" ? step.output.llm_used : undefined,
        llm_error: step.output?.llm_error ?? null,
        tool_calls: (d.tool_calls || []).map((tc: any) => ({
          node: tc.node,
          tool_name: tc.tool_name,
          status: tc.status,
          retry_count: tc.retry_count ?? 0,
          error: tc.error,
          latency_ms: tc.latency_ms,
          source: tc.source,
        })),
        skipped_nodes: step.output?.skipped_nodes || [],
        fallback_used: !!step.output?.fallback_used,
      })),
      final_answer: d.run.query || "",
    };
  }

  return (
    <AppShell title="Trace Viewer">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>Agent 执行链路</h2>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>查看 Agent 每次运行的完整执行链路和各阶段详细信息。</p>
        </div>
        {useMock && (
          <span className="badge-warning text-xs">使用 Mock Data</span>
        )}
      </div>

      {error && <div className="card mb-4 px-4 py-3 text-sm" style={{ color: "var(--error)", background: "var(--error-bg)" }}>{error}</div>}

      <div className="grid gap-6 lg:grid-cols-[340px_minmax(0,1fr)]">
        {/* Run list */}
        <section className="card h-fit">
          <div className="card-header flex items-center justify-between">
            <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>最近 Runs</h3>
            <span className="rounded-md px-2 py-0.5 text-xs" style={{ background: "var(--bg-subtle)", color: "var(--text-tertiary)" }}>
              {useMock ? "Mock" : runs.length}
            </span>
          </div>
          <div className="card-body space-y-2.5">
            {isLoadingRuns && <LoadingState message="正在加载..." />}
            {useMock && (
              <RunListItem
                run={{ run_id: "mock-001", query: "为什么订单接口报500？", route_type: "complex_troubleshooting", status: "success", total_latency_ms: 2103, created_at: new Date().toISOString() } as RunSummary}
                selected={true}
                onSelect={() => {}}
              />
            )}
            {!isLoadingRuns && !useMock && runs.length === 0 && <EmptyState title="暂无 Run" description="还没有执行过 Agent 任务。" />}
            {!useMock && runs.map((run) => (
              <RunListItem key={run.run_id} run={run} selected={run.run_id === selectedRunId} onSelect={setSelectedRunId} />
            ))}
          </div>
        </section>

        {/* Detail area */}
        <section className="min-w-0 space-y-4">
          {/* Loading state */}
          {isLoadingDetail && <LoadingState message="正在加载 Run 明细..." />}

          {/* Error state */}
          {detailError && !isLoadingDetail && (
            <div className="card px-4 py-4">
              <p className="text-sm font-medium" style={{ color: "var(--error)" }}>{detailError}</p>
              <button
                onClick={() => selectedRunId && fetchRun(selectedRunId).then(setDetail).catch(() => setDetailError("重试失败"))}
                className="mt-3 rounded-lg px-4 py-2 text-xs font-medium text-white"
                style={{ background: "var(--accent)" }}
              >
                重试
              </button>
            </div>
          )}

          {/* Detail content */}
          {hasDetail && (
            <>
              {/* Summary */}
              <div className="card">
                <div className="card-header">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="min-w-0">
                      <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                        {selectedRun?.query || detail?.run?.query || "—"}
                      </h3>
                      <p className="mt-0.5 font-mono text-xs" style={{ color: "var(--text-tertiary)" }}>
                        Run ID: {traceData?.trace_id || detail?.run?.run_id || "—"}
                      </p>
                    </div>
                    <StatusBadge
                      status={detail?.run?.status === "success" ? "success" : "pending"}
                      label={detail?.run?.status || "completed"}
                    />
                  </div>
                </div>
                <div className="card-body grid gap-3 sm:grid-cols-4">
                  <MetricCard label="Intent" value={detail?.run?.route_type === "complex_troubleshooting" ? "复杂排障" : "简单问答"} />
                  <MetricCard label="Total Latency" value={detail?.run?.total_latency_ms != null ? formatLatency(detail.run.total_latency_ms) : "—"} />
                  <MetricCard label="Tool Calls" value={String(detail?.tool_calls?.length ?? 0)} />
                  <MetricCard label="Answer Source" value={detail?.run?.answer_source === "llm" ? "DeepSeek" : "规则兜底"} />
                </div>
              </div>

              {/* Timeline */}
              {traceData && (
                <div className="card">
                  <div className="card-header">
                    <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Execution Timeline</h3>
                  </div>
                  <div className="card-body">
                    {steps.length === 0 ? (
                      <EmptyState title="无 Trace 数据" description="该 Run 没有记录执行链路。" />
                    ) : (
                      <div className="space-y-1">
                        {steps.map((step: TraceStep, i: number) => (
                          <TraceStepCard key={`${step.stage}-${i}`} step={step} index={i} />
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Empty state — no run selected */}
          {selectedRunId === "" && !isLoadingDetail && !detailError && (
            <EmptyState title="选择 Run" description="从左侧列表选择一个 Run 查看执行链路。" />
          )}

          {/* Detail fetch returned nothing — no data case */}
          {selectedRunId !== "" && !isLoadingDetail && !detailError && !hasDetail && (
            <EmptyState title="暂无详情数据" description="该 Run 没有返回详情数据。" />
          )}
        </section>
      </div>
    </AppShell>
  );
}
