"use client";

import { useEffect, useMemo, useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { TraceStepCard } from "@/components/trace/trace-step-card";
import { MetricCard } from "@/components/shared/metric-card";
import { StatusBadge } from "@/components/shared/status-badge";
import { LoadingState } from "@/components/shared/loading-state";
import { ErrorState } from "@/components/shared/error-state";
import { EmptyState } from "@/components/shared/empty-state";
import { fetchRun, fetchRuns, type RunSummary, type TraceStep } from "@/lib/api";
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
  const [detail, setDetail] = useState<any>(null);
  const [isLoadingRuns, setIsLoadingRuns] = useState(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [error, setError] = useState("");
  const [useMock, setUseMock] = useState(false);

  useEffect(() => {
    let mounted = true;
    setIsLoadingRuns(true);
    fetchRuns(50)
      .then((data) => {
        if (!mounted) return;
        if (data.length === 0) { setUseMock(true); return; }
        setRuns(data);
        setSelectedRunId(data[0].run_id);
      })
      .catch(() => { if (mounted) setUseMock(true); })
      .finally(() => { if (mounted) setIsLoadingRuns(false); });
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    if (!selectedRunId) { setDetail(null); return; }
    let mounted = true;
    setIsLoadingDetail(true);
    fetchRun(selectedRunId)
      .then((data) => { if (mounted) setDetail(data); })
      .catch(() => { if (mounted) setError("Run 明细加载失败。"); })
      .finally(() => { if (mounted) setIsLoadingDetail(false); });
    return () => { mounted = false; };
  }, [selectedRunId]);

  const traceData = useMock ? mockTraceData : detail?.trace;
  const steps = traceData?.steps ?? [];
  const selectedRun = runs.find((r) => r.run_id === selectedRunId);

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
          {isLoadingDetail && <LoadingState message="正在加载 Run 明细..." />}

          {!isLoadingDetail && traceData && (
            <>
              {/* Summary */}
              <div className="card">
                <div className="card-header">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="min-w-0">
                      <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                        {selectedRun?.query || "Mock Run: 为什么订单接口报500？"}
                      </h3>
                      <p className="mt-0.5 font-mono text-xs" style={{ color: "var(--text-tertiary)" }}>Run ID: {traceData.trace_id}</p>
                    </div>
                    <StatusBadge status="success" label="Completed" />
                  </div>
                </div>
                <div className="card-body grid gap-3 sm:grid-cols-4">
                  <MetricCard label="Intent" value={selectedRun?.route_type === "complex_troubleshooting" ? "复杂排障" : "—"} />
                  <MetricCard label="Total Latency" value={formatLatency(traceData.steps?.reduce((s: number, st: TraceStep) => s + (st.latency_ms ?? 0), 0))} />
                  <MetricCard label="Tools Used" value={String(traceData.steps?.find((s: TraceStep) => s.stage === "executor")?.tool_calls?.length ?? 0)} />
                  <MetricCard label="Model" value="DeepSeek v4 Flash" />
                </div>
              </div>

              {/* Timeline */}
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
            </>
          )}

          {!isLoadingDetail && !traceData && !error && (
            <EmptyState title="选择 Run" description="从左侧列表选择一个 Run 查看执行链路。" />
          )}
        </section>
      </div>
    </AppShell>
  );
}
