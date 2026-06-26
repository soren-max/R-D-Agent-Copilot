type EvaluationMetric = {
  label: string;
  score: number;
};

type EvaluationPanelProps = {
  evaluation?: {
    total_score?: number;
    metrics?: EvaluationMetric[];
  } | null;
};

const metricLabels: Record<string, string> = {
  tool_success_rate: "工具成功率",
  trace_completeness: "Trace 完整性",
  rag_relevance: "RAG 相关性",
  answer_grounding: "回答证据性",
  response_latency_score: "响应耗时评分",
};

function grade(score: number | undefined): { label: string; color: string } {
  if (score == null) return { label: "暂无", color: "text-slate-400" };
  if (score >= 85) return { label: "优秀", color: "text-emerald-600" };
  if (score >= 70) return { label: "良好", color: "text-blue-600" };
  if (score >= 50) return { label: "一般", color: "text-amber-600" };
  return { label: "需优化", color: "text-red-600" };
}

export function EvaluationPanel({ evaluation }: EvaluationPanelProps) {
  if (!evaluation) {
    return (
      <div className="card p-5">
        <h2 className="text-sm font-semibold text-slate-900">质量评估</h2>
        <p className="mt-4 text-sm text-slate-400">暂无数据</p>
      </div>
    );
  }

  const g = grade(evaluation.total_score);
  const metrics = evaluation.metrics ?? [];

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-900">质量评估</h2>
        <div className="flex items-center gap-2">
          <span className={`text-2xl font-bold ${g.color}`}>
            {evaluation.total_score ?? "-"}
          </span>
          <span className={`text-xs font-medium ${g.color}`}>{g.label}</span>
        </div>
      </div>
      {metrics.length > 0 && (
        <div className="mt-4 space-y-3">
          {metrics.map((m) => (
            <div key={m.label}>
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>{metricLabels[m.label] || m.label}</span>
                <span>{m.score}</span>
              </div>
              <div className="mt-1 h-1.5 w-full rounded-full bg-slate-100">
                <div
                  className="h-1.5 rounded-full bg-emerald-500 transition-all"
                  style={{ width: `${Math.min(m.score, 100)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
