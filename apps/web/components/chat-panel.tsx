import type { FormEvent } from "react";
import { AgentPipelineStepper } from "./agent-pipeline-stepper";

type ChatPanelProps = {
  query: string;
  isLoading: boolean;
  onQueryChange: (v: string) => void;
  onSubmit: (e: FormEvent<HTMLFormElement>) => void;
  onExample: (v: string) => void;
};

const demoCases: { label: string; query: string }[] = [
  { label: "📖 简单问答", query: "什么是配置中心？" },
  { label: "🔧 复杂排障", query: "为什么订单接口报500？配置改了但没有生效，应该怎么排查？" },
  { label: "⚠️ 证据不足", query: "项目里没有覆盖的未知系统故障应该怎么处理？" },
];

export function ChatPanel({ query, isLoading, onQueryChange, onSubmit, onExample }: ChatPanelProps) {
  return (
    <div className="card">
      <form onSubmit={onSubmit}>
        <div className="card-header">
          <label htmlFor="query" className="text-base font-semibold" style={{color:"var(--text-primary)"}}>
            研发问题输入
          </label>
          <p className="mt-1 text-xs" style={{color:"var(--text-tertiary)"}}>输入一个研发问题，Agent 会执行完整排障链路并返回可追踪报告。</p>
        </div>
        <div className="card-body space-y-4">
          {/* Execution path stepper */}
          <div className="rounded-xl px-4 py-3" style={{background:"var(--bg-subtle)"}}>
            <p className="text-[10px] font-semibold uppercase tracking-wider mb-2" style={{color:"var(--text-tertiary)"}}>Agent Execution Path</p>
            <AgentPipelineStepper />
          </div>

          <textarea
            id="query"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            placeholder="例如：为什么订单接口报500？配置改了但没有生效，应该怎么排查？"
            rows={4}
            className="w-full resize-y rounded-xl border px-4 py-3 text-sm leading-6 transition-colors"
            style={{borderColor:"var(--border)",background:"var(--bg-subtle)",color:"var(--text-primary)"}}
          />

          <div className="flex flex-wrap items-center gap-2.5">
            <button
              type="submit"
              disabled={isLoading}
              className="inline-flex min-h-10 items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-all hover:opacity-90 active:scale-[0.98] disabled:cursor-not-allowed disabled:bg-slate-300"
              style={{background: isLoading ? "var(--text-muted)" : "var(--accent)"}}
            >
              {isLoading ? (
                <><svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>Agent 分析中...</>
              ) : "开始排查"}
            </button>

            {/* Demo case buttons */}
            {demoCases.map((dc) => (
              <button
                key={dc.query}
                type="button"
                onClick={() => { onQueryChange(dc.query); onExample(dc.query); }}
                disabled={isLoading}
                className="rounded-xl border px-3 py-2 text-xs font-medium transition-all disabled:opacity-50"
                style={{borderColor:"var(--border)",color:"var(--text-secondary)",background:"var(--bg-card)"}}
              >
                {dc.label}
              </button>
            ))}
          </div>

          {isLoading && (
            <div className="rounded-xl px-4 py-3 text-xs font-medium" style={{color:"var(--accent)",background:"var(--accent-light)"}}>
              Router → Planner → LangGraph Tools → Synthesizer → Evaluation
            </div>
          )}
        </div>
      </form>
    </div>
  );
}
