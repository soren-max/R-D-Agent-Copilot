type AnswerCardProps = {
  answer: string;
  answerSource?: string;
  llmUsed?: boolean;
  llmError?: string | null;
};

export function AnswerCard({ answer, answerSource, llmUsed, llmError }: AnswerCardProps) {
  const sourceLabel =
    answerSource === "llm" ? "DeepSeek 生成" : "规则兜底";
  const llmLabel = llmUsed ? "LLM 已启用" : "LLM 未启用";

  return (
    <section className="card card-interactive overflow-hidden">
      <div className="card-header">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-slate-950">Agent 排障报告</h2>
            <p className="mt-1 text-xs text-slate-500">基于工具证据和知识库检索生成的中文排障报告。</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
          <span
            className={`badge ${
              answerSource === "llm" ? "badge-blue" : "badge-slate"
            }`}
          >
            {sourceLabel}
          </span>
          <span className={`badge ${llmUsed ? "badge-green" : "badge-slate"}`}>
            {llmLabel}
          </span>
          </div>
        </div>
      </div>
      <div className="card-body">
        <div className="rounded-2xl border-l-4 border-emerald-400 bg-slate-50/70 px-4 py-4">
          <p className="whitespace-pre-wrap text-sm leading-7 text-slate-800">{answer || "暂无数据"}</p>
        </div>
        {llmError && (
          <p className="mt-3 rounded-xl border border-amber-100 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-700">
            LLM 状态：{llmError}
          </p>
        )}
      </div>
    </section>
  );
}
