import type { PersistedRunStep, PersistedToolCall } from "@/lib/api";
import { StatusBadge } from "@/components/shared/status-badge";
import { JsonViewer } from "@/components/shared/json-viewer";

type Props = {
  steps?: PersistedRunStep[];
  toolCalls?: PersistedToolCall[];
};

export function TraceTimeline({ steps, toolCalls }: Props) {
  if (!steps || steps.length === 0) return null;
  const stageColors: Record<string,string> = {router:"#6366f1",planner:"#0284c7",executor:"#d97706",synthesizer:"#8b5cf6",evaluation:"#059669"};
  const stageIcons: Record<string,string> = {router:"▶",planner:"◎",executor:"⚙",synthesizer:"◆",evaluation:"◉"};
  return (
    <div className="card">
      <div className="card-header"><h3 className="text-sm font-semibold" style={{color:"var(--text-primary)"}}>Execution Timeline</h3></div>
      <div className="card-body">
        {steps.map((step,i)=>{
          const color = stageColors[step.stage ?? ""] || "#64748b";
          const icon = stageIcons[step.stage ?? ""] || "●";
          return (
            <div key={i} className="relative flex gap-4 pb-5 last:pb-0">
              {i < steps.length - 1 && <div className="absolute left-[19px] top-4 h-full w-0.5" style={{background:"var(--border)"}} />}
              <div className="relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-sm font-bold text-white" style={{background:color}}>{icon}</div>
              <div className="min-w-0 flex-1 rounded-xl border px-4 py-3" style={{borderColor:"var(--border)"}}>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold" style={{color:"var(--text-primary)"}}>{step.stage || "—"}</span>
                    <StatusBadge status={step.status === "success" ? "success" : step.status === "failed" ? "error" : "pending"} label={step.status ?? "—"} />
                  </div>
                  <div className="flex items-center gap-2 text-xs" style={{color:"var(--text-tertiary)"}}>
                    {step.latency_ms != null && <span>{step.latency_ms}ms</span>}
                    {step.engine && <span className="rounded-md px-2 py-0.5" style={{background:"var(--accent-light)",color:"var(--accent)"}}>{step.engine}</span>}
                  </div>
                </div>
                {step.output && (
                  <p className="mt-2 text-xs leading-5 line-clamp-2" style={{color:"var(--text-secondary)"}}>
                    {typeof step.output === "object" ? JSON.stringify(step.output).slice(0,200) : String(step.output).slice(0,200)}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
