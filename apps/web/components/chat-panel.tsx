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
    <div className="card p-5">
      <form onSubmit={onSubmit}>
        <label htmlFor="query" className="text-sm font-semibold text-slate-900">
          研发问题输入
        </label>
        <textarea
          id="query"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder="例如：为什么订单接口报500？配置改了但没有生效，应该怎么排查？"
          rows={4}
          className="mt-3 w-full resize-y rounded-xl border border-slate-200 bg-slate-50/50 px-4 py-3 text-sm leading-6 text-slate-900 placeholder:text-slate-400 transition-colors focus:bg-white focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400"
        />
        <div className="mt-4 flex flex-wrap items-center gap-2.5">
          <button
            type="submit"
            disabled={isLoading}
            className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-emerald-700 active:scale-[0.98] disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none"
          >
            {isLoading ? (
              <>
                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
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
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-600 transition-colors hover:border-emerald-300 hover:text-emerald-700 disabled:opacity-50"
            >
              {ex}
            </button>
          ))}
        </div>
      </form>
      {isLoading && (
        <p className="mt-4 text-xs text-slate-400">
          正在执行 Router → Planner → LangGraph Tools → Synthesizer
        </p>
      )}
    </div>
  );
}
