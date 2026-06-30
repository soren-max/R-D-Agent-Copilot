import type { EvaluationMetrics, EvaluationResult, LatencyBreakdown } from "@/lib/api";

type EvaluationPanelProps = {
  evaluation?: EvaluationResult | null;
};

const metricLabels: Record<keyof EvaluationMetrics, string> = {
  tool_success_rate: "工具成功率",
  trace_completeness: "Trace 完整性",
  rag_relevance: "知识库相关性",
  answer_groundedness: "回答证据性",
  latency_score: "响应耗时评分",
  evidence_confidence_score: "证据链置信度",
};

function toPercent(value: number | null | undefined) {
  if (typeof value !== "number" || Number.isNaN(value)) return "—";
  return `${Math.round(value * 100)}%`;
}

function scoreLevel(score: number | undefined) {
  if (typeof score !== "number") return { label: "未评估", color: "text-slate-400" };
  if (score >= 0.85) return { label: "优秀", color: "text-emerald-600" };
  if (score >= 0.70) return { label: "良好", color: "text-blue-600" };
  if (score >= 0.50) return { label: "一般", color: "text-amber-600" };
  return { label: "需优化", color: "text-red-600" };
}

type LatencyMsKey =
  | "router_ms"
  | "planner_ms"
  | "executor_ms"
  | "tools_ms"
  | "synthesizer_ms"
  | "evaluation_ms";

const latencyLabels: Array<[LatencyMsKey, string]> = [
  ["router_ms", "Router"],
  ["planner_ms", "Planner"],
  ["executor_ms", "LangGraph Executor"],
  ["tools_ms", "Tools"],
  ["synthesizer_ms", "DeepSeek Synthesizer"],
  ["evaluation_ms", "Evaluation"],
];

function formatMs(value: number | undefined) {
  if (typeof value !== "number" || Number.isNaN(value)) return "0ms";
  return `${Math.round(value)}ms`;
}

function bottleneckLabel(stage: string | undefined) {
  if (stage === "router") return "Router";
  if (stage === "planner") return "Planner";
  if (stage === "executor") return "LangGraph Executor";
  if (stage === "tools") return "Tools";
  if (stage === "synthesizer") return "DeepSeek Synthesizer";
  if (stage === "evaluation") return "Evaluation";
  return "未识别";
}

export function EvaluationPanel({ evaluation }: EvaluationPanelProps) {
  if (!evaluation) {
    return (
      <div className="card">
        <div className="card-header">
          <h2 className="text-base font-semibold text-slate-950">Evaluation Panel Pro</h2>
        </div>
        <div className="card-body">
          <p className="text-sm text-slate-400">暂无数据</p>
        </div>
      </div>
    );
  }

  const level = scoreLevel(evaluation.overall_score);
  const metrics = evaluation.metrics || {};
  const latency = evaluation.latency_breakdown;
  const issues = evaluation.issues || [];
  const suggestions = evaluation.suggestions || [];

  return (
    <section className="card">
      <div className="card-header">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-slate-950">Evaluation Panel Pro</h2>
            <p className="mt-1 text-xs text-slate-500">基于 rule-based 评估结果，仅用于本地演示和质量参考。</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2 text-right">
            <span className={`block text-2xl font-bold ${level.color}`}>
              {toPercent(evaluation.overall_score)}
            </span>
            <span className={`text-xs font-semibold ${level.color}`}>{level.label}</span>
          </div>
        </div>
      </div>
      <div className="card-body space-y-4">
        <div className="grid gap-3 sm:grid-cols-2">
          {(Object.keys(metricLabels) as Array<keyof EvaluationMetrics>).map((key) => {
            const v = metrics[key];
            const pct = Math.max(0, Math.min(100, Math.round((v ?? 0) * 100)));
            return (
              <div key={key} className="rounded-2xl border border-slate-100 bg-slate-50/70 px-3 py-3">
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span className="font-medium">{metricLabels[key]}</span>
                  <span className="font-semibold tabular-nums text-slate-700">{toPercent(v)}</span>
                </div>
                <div className="mt-2 h-1.5 w-full rounded-full bg-white">
                  <div className="h-1.5 rounded-full bg-emerald-500" style={{ width: `${pct}%` }} />
                </div>
              </div>
            );
          })}
        </div>

        {latency && (
          <div className="rounded-2xl border border-slate-100 bg-white p-4">
            <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-xs font-semibold text-slate-700">耗时拆解</h3>
              <span className="badge-slate">
                瓶颈: {bottleneckLabel(latency.bottleneck_stage)} · {formatMs(latency.bottleneck_ms)}
              </span>
            </div>
            <div className="space-y-2">
              {latencyLabels.map(([key, label]) => {
                const value = latency[key];
                const total = Math.max(latency.total_ms ?? 0, 1);
                const pct = Math.min(100, Math.round(((value ?? 0) / total) * 100));
                return (
                  <div key={key}>
                    <div className="flex items-center justify-between text-xs text-slate-500">
                      <span>{label}</span>
                      <span>{formatMs(value)}</span>
                    </div>
                    <div className="mt-1 h-1.5 w-full rounded-full bg-slate-100">
                      <div className="h-1.5 rounded-full bg-blue-500" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
            <p className="mt-3 text-xs leading-5 text-slate-400">
              总耗时 {formatMs(latency.total_ms)}，Tools 为各工具调用耗时之和，用于区分工具执行与 LLM 生成成本。
            </p>
          </div>
        )}

        {issues.length > 0 && (
          <div>
            <h3 className="mb-1.5 text-xs font-semibold text-slate-700">发现的问题</h3>
            <ul className="space-y-1">
              {issues.map((issue) => (
                <li key={issue} className="rounded-xl border border-red-100 bg-red-50/50 px-3 py-2 text-xs text-red-700">{issue}</li>
              ))}
            </ul>
          </div>
        )}

        {suggestions.length > 0 && (
          <div>
            <h3 className="mb-1.5 text-xs font-semibold text-slate-700">优化建议</h3>
            <ul className="space-y-1">
              {suggestions.map((s) => (
                <li key={s} className="rounded-xl border border-amber-100 bg-amber-50/50 px-3 py-2 text-xs text-amber-700">{s}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </section>
  );
}
