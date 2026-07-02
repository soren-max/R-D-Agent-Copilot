import type { FormEvent } from "react";

type ChatPanelProps = {
  query: string;
  isLoading: boolean;
  onQueryChange: (v: string) => void;
  onSubmit: (e: FormEvent<HTMLFormElement>) => void;
  onExample: (v: string) => void;
};

const examples = [
  "什么是配置中心？",
  "为什么订单接口报500？",
  "配置改了为什么不生效？",
];

export function ChatPanel({ query, isLoading, onQueryChange, onSubmit, onExample }: ChatPanelProps) {
  return (
    <div className="card card-interactive">
      <form onSubmit={onSubmit}>
        <div className="card-header">
          <label htmlFor="query" className="text-base font-semibold text-slate-950">
            研发问题输入
          </label>
          <p className="mt-1 text-xs text-slate-500">输入一个研发问题，Agent 会执行完整排障链路并返回可追踪报告。</p>
        </div>
        <div className="card-body">
          <textarea
            id="query"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            placeholder="例如：为什么订单接口报500？配置改了但没有生效，应该怎么排查？"
            rows={5}
            className="w-full resize-y rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 text-sm leading-6 text-slate-900 placeholder:text-slate-400 transition-colors focus:border-emerald-400 focus:bg-white focus:ring-2 focus:ring-emerald-500/20"
          />
          <div className="mt-4 flex flex-wrap items-center gap-2.5">
            <button
              type="submit"
              disabled={isLoading}
              className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-indigo-700 active:scale-[0.98] disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none"
            >
              {isLoading ? (
                <>
                  <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Agent 分析中...
                </>
              ) : (
                "开始排查"
              )}
            </button>
            {examples.map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => onExample(ex)}
                disabled={isLoading}
                className="min-h-10 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-600 transition-all hover:border-indigo-300 hover:bg-indigo-50/50 hover:text-indigo-700 disabled:opacity-50"
              >
                {ex}
              </button>
            ))}
          </div>
          {isLoading && (
            <div className="mt-4 rounded-2xl border border-emerald-100 bg-emerald-50/60 px-4 py-3 text-xs font-medium text-emerald-700">
              Router → Planner → LangGraph Tools → Synthesizer → Evaluation
            </div>
          )}
        </div>
      </form>
    </div>
  );
}
