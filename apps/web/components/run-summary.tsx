import type { ChatResponse, LatencyBreakdown } from "@/lib/api";

type RunSummaryProps = {
  result?: ChatResponse | null;
  isLoading?: boolean;
};

type LatencyMsKey =
  | "router_ms"
  | "planner_ms"
  | "executor_ms"
  | "tools_ms"
  | "synthesizer_ms"
  | "evaluation_ms";

const latencyItems: Array<[LatencyMsKey, string]> = [
  ["router_ms", "Router"],
  ["planner_ms", "Planner"],
  ["executor_ms", "Executor"],
  ["tools_ms", "Tools"],
  ["synthesizer_ms", "Synthesizer"],
  ["evaluation_ms", "Evaluation"],
];

function routeLabel(value?: string) {
  if (value === "simple_qa") return "简单问答";
  if (value === "complex_troubleshooting") return "复杂排障";
  return value || "暂无数据";
}

function answerSource(value?: string) {
  if (value === "llm") return "DeepSeek 生成";
  if (value === "fallback") return "规则兜底";
  return value || "暂无数据";
}

function formatMs(value?: number) {
  if (typeof value !== "number") return "0ms";
  return `${Math.round(value)}ms`;
}

function scoreText(value?: number) {
  if (typeof value !== "number") return "暂无数据";
  return `${Math.round(value * 100)}%`;
}

export function RunSummary({ result, isLoading = false }: RunSummaryProps) {
  const traceSteps = result?.trace?.steps ?? [];
  const latency = result?.evaluation?.latency_breakdown;
  const totalMs = latency?.total_ms ?? traceSteps.reduce((sum, step) => sum + (step.latency_ms ?? 0), 0);

  return (
    <div className="space-y-4">
      <section className="card card-interactive">
        <div className="card-header">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-sm font-semibold text-slate-950">Current Run</h2>
            <span className={isLoading ? "badge-amber" : result ? "badge-green" : "badge-slate"}>
              <span className={isLoading ? "dot-amber" : result ? "dot-green" : "dot-slate"} />
              {isLoading ? "Running" : result ? "Ready" : "Idle"}
            </span>
          </div>
        </div>
        <div className="card-body space-y-3">
          <SummaryRow label="Trace ID" value={result?.trace?.trace_id || "暂无数据"} mono />
          <SummaryRow label="Route" value={routeLabel(result?.route?.type)} />
          <SummaryRow label="Answer Source" value={answerSource(result?.answer_source)} />
          <SummaryRow label="Quality Score" value={scoreText(result?.evaluation?.overall_score)} />
          <SummaryRow label="Tool Calls" value={String(result?.tool_results?.length ?? 0)} />
          <SummaryRow label="Total Latency" value={formatMs(totalMs)} />
        </div>
      </section>

      <section className="card card-interactive">
        <div className="card-header">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-sm font-semibold text-slate-950">Latency Breakdown</h2>
            <span className="badge-slate">{formatMs(totalMs)}</span>
          </div>
        </div>
        <div className="card-body space-y-3">
          {latency ? (
            <>
              {latencyItems.map(([key, label]) => {
                const value = latency[key] ?? 0;
                const pct = Math.min(100, Math.round((value / Math.max(totalMs, 1)) * 100));
                return (
                  <div key={key}>
                    <div className="flex items-center justify-between text-xs text-slate-500">
                      <span>{label}</span>
                      <span className="tabular-nums">{formatMs(value)}</span>
                    </div>
                    <div className="mt-1.5 h-1.5 rounded-full bg-slate-100">
                      <div className="h-1.5 rounded-full bg-sky-500" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </>
          ) : (
            <p className="text-sm text-slate-400">暂无数据</p>
          )}
        </div>
      </section>
    </div>
  );
}

function SummaryRow({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-slate-100 pb-2.5 last:border-b-0 last:pb-0">
      <span className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</span>
      <span className={`max-w-[11rem] text-right text-xs font-semibold text-slate-800 ${mono ? "font-mono" : ""}`}>
        {value}
      </span>
    </div>
  );
}
