import type { EvaluationMetrics, EvaluationResult } from "@/lib/api";

type EvaluationPanelProps = {
  evaluation?: EvaluationResult | null;
};

const metricLabels: Record<keyof EvaluationMetrics, string> = {
  tool_success_rate: "工具成功率",
  trace_completeness: "Trace 完整性",
  rag_relevance: "知识库相关性",
  answer_groundedness: "回答证据性",
  latency_score: "响应耗时评分",
};

function toPercent(value: number | undefined) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "未记录";
  }
  return `${Math.round(value * 100)}%`;
}

function scoreLevel(score: number | undefined) {
  if (typeof score !== "number") {
    return "未评估";
  }
  if (score >= 0.85) {
    return "优秀";
  }
  if (score >= 0.7) {
    return "良好";
  }
  if (score >= 0.5) {
    return "一般";
  }
  return "需优化";
}

function MetricRow({ label, value }: { label: string; value: number | undefined }) {
  const percent = Math.max(0, Math.min(100, Math.round((value ?? 0) * 100)));

  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm font-medium text-slate-700">{label}</span>
        <span className="text-sm font-semibold text-slate-950">{toPercent(value)}</span>
      </div>
      <div className="mt-2 h-2 rounded-full bg-white">
        <div className="h-2 rounded-full bg-emerald-600" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}

export function EvaluationPanel({ evaluation }: EvaluationPanelProps) {
  if (!evaluation) {
    return (
      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-950">Agent 质量评估</h2>
        <p className="mt-3 text-sm text-slate-600">暂无评估结果。</p>
      </section>
    );
  }

  const metrics = evaluation.metrics || {};
  const issues = evaluation.issues || [];
  const suggestions = evaluation.suggestions || [];

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-lg font-semibold text-slate-950">Agent 质量评估</h2>
        <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
          {scoreLevel(evaluation.overall_score)}
        </span>
      </div>

      <div className="mt-4 rounded-md border border-emerald-100 bg-emerald-50 p-4">
        <p className="text-sm text-emerald-800">Agent 质量评分</p>
        <p className="mt-1 text-3xl font-semibold text-emerald-900">
          {toPercent(evaluation.overall_score)}
        </p>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {(Object.keys(metricLabels) as Array<keyof EvaluationMetrics>).map((key) => (
          <MetricRow key={key} label={metricLabels[key]} value={metrics[key]} />
        ))}
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <div>
          <h3 className="text-sm font-semibold text-slate-950">发现的问题</h3>
          {issues.length > 0 ? (
            <ul className="mt-3 space-y-2 text-sm text-slate-700">
              {issues.map((issue) => (
                <li key={issue} className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2">
                  {issue}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600">
              暂无明显问题。
            </p>
          )}
        </div>

        <div>
          <h3 className="text-sm font-semibold text-slate-950">优化建议</h3>
          {suggestions.length > 0 ? (
            <ul className="mt-3 space-y-2 text-sm text-slate-700">
              {suggestions.map((suggestion) => (
                <li
                  key={suggestion}
                  className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2"
                >
                  {suggestion}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600">
              暂无明显问题。
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
