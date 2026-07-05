import { useState } from "react";
import type { PersistedRunStep, PersistedToolCall } from "@/lib/api";
import { StatusBadge } from "@/components/shared/status-badge";

type Props = { steps?: PersistedRunStep[]; toolCalls?: PersistedToolCall[] };

const stageColors: Record<string,string> = {router:"#6366f1",planner:"#0284c7",executor:"#d97706",synthesizer:"#8b5cf6",evaluation:"#059669"};
const stageIcons: Record<string,string> = {router:"▶",planner:"◎",executor:"⚙",synthesizer:"◆",evaluation:"◉"};

function summarize(v: unknown, max=160): string {
  if (!v) return "";
  const s = typeof v === "object" ? JSON.stringify(v) : String(v);
  return s.length > max ? s.slice(0,max)+"…" : s;
}

function ToolCallLabel({ name, status, latency, error }: { name?: string; status?: string; latency?: number; error?: string }) {
  return (
    <div className="flex flex-wrap items-center gap-2 rounded-lg px-3 py-2 text-xs" style={{background:"var(--bg-subtle)"}}>
      <span className="font-medium" style={{color:"var(--text-primary)"}}>{name || "—"}</span>
      <StatusBadge status={status === "success" ? "success" : status === "failed" ? "error" : "pending"} label={status ?? "—"} />
      {latency != null && <span style={{color:"var(--text-tertiary)"}}>{latency}ms</span>}
      {error && <span style={{color:"var(--error)"}}>error: {error}</span>}
    </div>
  );
}

export function TraceTimeline({ steps, toolCalls }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);
  if (!steps || steps.length === 0) return null;

  return (
    <div className="card">
      <div className="card-header"><h3 className="text-sm font-semibold" style={{color:"var(--text-primary)"}}>Execution Timeline</h3></div>
      <div className="card-body">
        {steps.map((step,i)=>{
          const color = stageColors[step.stage ?? ""] || "#64748b";
          const icon = stageIcons[step.stage ?? ""] || "●";
          const key = `step-${i}`;
          const open = expanded === key;
          const output = typeof step.output === "object" ? step.output as Record<string,unknown> : {};
          const toolNames: string[] = (output.tool_calls as any[])?.map((t:any)=>t.tool_name||t.tool||"?").filter(Boolean) || [];

          return (
            <div key={i} className="relative flex gap-4 pb-5 last:pb-0">
              {i < steps.length - 1 && <div className="absolute left-[19px] top-4 h-full w-0.5" style={{background:"var(--border)"}} />}
              <div className="relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-sm font-bold text-white" style={{background:color}}>{icon}</div>
              <div className="min-w-0 flex-1">
                <div className="cursor-pointer rounded-xl border px-4 py-3 transition-all hover:shadow-sm" style={{borderColor:"var(--border)"}} onClick={() => setExpanded(open ? null : key)}>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold" style={{color:"var(--text-primary)"}}>{step.stage || "—"}</span>
                      <StatusBadge status={step.status === "success" ? "success" : step.status === "failed" ? "error" : "pending"} label={step.status ?? "—"} />
                    </div>
                    <div className="flex items-center gap-2 text-xs" style={{color:"var(--text-tertiary)"}}>
                      {step.latency_ms != null && <span>{step.latency_ms}ms</span>}
                      {step.engine && <span className="rounded-md px-2 py-0.5" style={{background:"var(--accent-light)",color:"var(--accent)"}}>{step.engine}</span>}
                      <span>{open ? "▲" : "▼"}</span>
                    </div>
                  </div>

                  {/* Summary line: tool names */}
                  {toolNames.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {toolNames.map(t => <span key={t} className="rounded-md px-2 py-0.5 text-xs" style={{background:"var(--bg-subtle)",color:"var(--text-secondary)"}}>{t}</span>)}
                    </div>
                  )}

                  {/* Collapsed: one-line output */}
                  {!open && step.output && (
                    <p className="mt-2 text-xs leading-5 truncate" style={{color:"var(--text-secondary)"}}>
                      {summarize(step.output)}
                    </p>
                  )}

                  {/* Expanded detail */}
                  {open && (
                    <div className="mt-3 space-y-3 border-t pt-3" style={{borderColor:"var(--border-light)"}}>
                      {/* Input summary */}
                      {step.input && (
                        <div>
                          <p className="mb-1 text-xs font-semibold" style={{color:"var(--text-tertiary)"}}>Input</p>
                          <p className="rounded-lg px-3 py-2 text-xs" style={{background:"var(--bg-subtle)",color:"var(--text-secondary)"}}>{summarize(step.input, 300)}</p>
                        </div>
                      )}
                      {/* Output summary */}
                      {step.output && (
                        <div>
                          <p className="mb-1 text-xs font-semibold" style={{color:"var(--text-tertiary)"}}>Output</p>
                          <p className="rounded-lg px-3 py-2 text-xs" style={{background:"var(--bg-subtle)",color:"var(--text-secondary)"}}>{summarize(step.output, 400)}</p>
                        </div>
                      )}
                      {/* Tool calls from this step */}
                      {toolNames.length > 0 && (
                        <div>
                          <p className="mb-1 text-xs font-semibold" style={{color:"var(--text-tertiary)"}}>Tools ({toolNames.length})</p>
                          <div className="space-y-1">
                            {toolNames.map(t => <ToolCallLabel key={t} name={t} status="success" />)}
                          </div>
                        </div>
                      )}
                      {/* Global tool calls (executor stage) */}
                      {step.stage === "executor" && toolCalls && toolCalls.length > 0 && (
                        <div>
                          <p className="mb-1 text-xs font-semibold" style={{color:"var(--text-tertiary)"}}>Persisted Tool Calls ({toolCalls.length})</p>
                          <div className="space-y-1">
                            {toolCalls.filter(tc => tc.status === "success" || tc.status === "failed").map((tc,i) => (
                              <ToolCallLabel key={i} name={tc.tool_name ?? tc.node ?? "—"} status={tc.status ?? "—"} latency={tc.latency_ms ?? undefined} error={tc.error ?? undefined} />
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
