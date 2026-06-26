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

export function EvaluationPanel({ evaluation }: EvaluationPanelProps) {
  if (!evaluation) {
    return (
      <div className="card">
        <div className="card-header">
          <h2 className="text-sm font-semibold text-slate-900">质量评估</h2>
        </div>
        <div className="card-body">
          <p className="text-sm text-slate-400">暂无数据</p>
        </div>
      </div>
    );
  }

  const level = scoreLevel(evaluation.overall_score);
  const metrics = evaluation.metrics || {};
  const issues = evaluation.issues || [];
  const suggestions = evaluation.suggestions || [];

  return (
    <div className="card">
      <div className="card-header">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900">质量评估</h2>
          <div className="flex items-center gap-2">
            <span className={`text-xl font-bold ${level.color}`}>
              {toPercent(evaluation.overall_score)}
            </span>
            <span className={`text-xs font-medium ${level.color}`}>{level.label}</span>
          </div>
        </div>
      </div>
      <div className="card-body space-y-4">
        {/* Metrics */}
        <div className="grid gap-2.5 sm:grid-cols-2">
          {(Object.keys(metricLabels) as Array<keyof EvaluationMetrics>).map((key) => {
            const v = metrics[key];
            const pct = Math.max(0, Math.min(100, Math.round((v ?? 0) * 100)));
            return (
              <div key={key}>
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span>{metricLabels[key]}</span>
                  <span>{toPercent(v)}</span>
                </div>
                <div className="mt-1 h-1.5 w-full rounded-full bg-slate-100">
                  <div className="h-1.5 rounded-full bg-emerald-500" style={{ width: `${pct}%` }} />
                </div>
              </div>
            );
          })}
        </div>

        {/* Issues */}
        {issues.length > 0 && (
          <div>
            <h3 className="mb-1.5 text-xs font-semibold text-slate-700">发现的问题</h3>
            <ul className="space-y-1">
              {issues.map((issue) => (
                <li key={issue} className="rounded-lg border border-red-100 bg-red-50/40 px-3 py-2 text-xs text-red-700">{issue}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Suggestions */}
        {suggestions.length > 0 && (
          <div>
            <h3 className="mb-1.5 text-xs font-semibold text-slate-700">优化建议</h3>
            <ul className="space-y-1">
              {suggestions.map((s) => (
                <li key={s} className="rounded-lg border border-amber-100 bg-amber-50/40 px-3 py-2 text-xs text-amber-700">{s}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Disclaimer */}
        <p className="text-xs text-slate-400 leading-relaxed">
          基于 rule-based 评估结果，仅用于本地演示和质量参考。
        </p>
      </div>
    </div>
  );
}
