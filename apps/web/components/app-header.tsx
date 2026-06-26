import type { TraceData, EvaluationResult, ToolResult } from "@/lib/api";

type AppHeaderProps = {
  evaluation?: EvaluationResult | null;
  trace?: TraceData;
  toolResults?: ToolResult[];
};

export function AppHeader({ evaluation, trace, toolResults }: AppHeaderProps) {
  const toolCount = toolResults?.length ?? 0;
  const evalScore = evaluation?.overall_score;
  const evalPct = typeof evalScore === "number" ? `${Math.round(evalScore * 100)}%` : null;

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3 lg:px-8">
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-slate-900">
            R&D Agent Copilot
          </h1>
          <p className="text-xs text-slate-400">AI 研发排障智能助手</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="badge-green"><span className="dot-green" /> LangGraph</span>
          <span className="badge-slate"><span className="dot-green" /> LocalAdapter</span>
          <span className="badge-blue"><span className="dot-amber" /> DeepSeek Optional</span>
          <span className="badge-green"><span className="dot-green" /> Trace</span>
          {evalPct && (
            <span className="badge-green">评分 {evalPct}</span>
          )}
          {toolCount > 0 && (
            <span className="badge-slate">{toolCount} 工具</span>
          )}
        </div>
      </div>
    </header>
  );
}
