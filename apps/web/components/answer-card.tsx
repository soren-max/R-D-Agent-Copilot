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
    <div className="card overflow-hidden">
      <div className="border-b border-slate-100 bg-gradient-to-r from-emerald-50/30 to-transparent px-5 py-4">
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="text-sm font-semibold text-slate-900">Agent 排障报告</h2>
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
      <div className="px-5 py-4">
        <p className="whitespace-pre-wrap text-sm leading-7 text-slate-800">{answer}</p>
        {llmError && (
          <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">
            LLM 状态：{llmError}
          </p>
        )}
      </div>
    </div>
  );
}
