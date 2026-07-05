"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { AppShell } from "@/components/layout/app-shell";
import { MetricCard } from "@/components/shared/metric-card";
import { StatusBadge } from "@/components/shared/status-badge";
import { LoadingState } from "@/components/shared/loading-state";
import { ErrorState } from "@/components/shared/error-state";
import { EmptyState } from "@/components/shared/empty-state";
import { FinalReportCard } from "@/components/run/final-report-card";
import { TraceTimeline } from "@/components/run/trace-timeline";
import { ContextMetadataCard } from "@/components/run/context-metadata-card";
import { IncidentMemoryCard } from "@/components/run/incident-memory-card";
import { CheckpointCard } from "@/components/run/checkpoint-card";
import { EvaluationV2Panel } from "@/components/run/evaluation-v2-panel";
import { ProviderMetadataCard } from "@/components/run/provider-metadata-card";
import { fetchRun, type RunDetail } from "@/lib/api";

export default function RunDetailPage() {
  const params = useParams();
  const runId = params?.runId as string;
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!runId) return;
    setLoading(true); setError(null);
    fetchRun(runId)
      .then(setDetail)
      .catch(() => setError("Run 详情加载失败。"))
      .finally(() => setLoading(false));
  }, [runId]);

  const r = detail?.run;

  return (
    <AppShell title="Run Detail">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold" style={{color:"var(--text-primary)"}}>Run Detail</h2>
          <p className="text-sm" style={{color:"var(--text-secondary)"}}>Agent Harness 全链路详情。</p>
        </div>
        <Link href="/runs" className="rounded-xl border px-4 py-2 text-xs font-medium" style={{borderColor:"var(--border)",color:"var(--text-secondary)"}}>← Back to Runs</Link>
      </div>

      {loading && <LoadingState message="加载 Run 详情..." />}
      {error && <ErrorState message={error} onRetry={() => { setLoading(true); setError(null); fetchRun(runId).then(setDetail).catch(() => setError("重试失败")).finally(() => setLoading(false)); }} />}

      {!loading && !error && !detail && <EmptyState title="No Data" description="该 Run 没有返回详情。" />}

      {detail && (
        <div className="space-y-5">
          {/* Summary */}
          <div className="card">
            <div className="card-header">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="min-w-0">
                  <h3 className="text-sm font-semibold" style={{color:"var(--text-primary)"}}>{r?.query || "—"}</h3>
                  <p className="mt-0.5 font-mono text-xs" style={{color:"var(--text-tertiary)"}}>Run ID: {r?.run_id}</p>
                </div>
                <StatusBadge status={r?.status === "success" ? "success" : "pending"} label={r?.status || "—"} />
              </div>
            </div>
            <div className="card-body grid gap-3 sm:grid-cols-4">
              <MetricCard label="Intent" value={r?.route_type === "complex_troubleshooting" ? "复杂排障" : "简单问答"} />
              <MetricCard label="Latency" value={r?.total_latency_ms != null ? `${r.total_latency_ms}ms` : "—"} />
              <MetricCard label="Answer Source" value={r?.answer_source === "llm" ? "DeepSeek" : "规则兜底"} />
              <MetricCard label="Steps" value={detail.steps?.length ?? 0} />
            </div>
          </div>

          {/* Harness panels */}
          <FinalReportCard report={detail.final_report} />
          <TraceTimeline steps={detail.steps} toolCalls={detail.tool_calls} />
          <ContextMetadataCard metadata={detail.context_metadata} />
          <IncidentMemoryCard memory={detail.incident_memory} />
          <CheckpointCard checkpoint={detail.checkpoint} />
          <EvaluationV2Panel evaluationV2={detail.evaluation_v2} />
          <ProviderMetadataCard metadata={detail.provider_metadata} />
        </div>
      )}
    </AppShell>
  );
}
