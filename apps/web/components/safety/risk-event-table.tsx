import { useState } from "react";
import type { RiskEvent } from "@/lib/mock/safety";
import { RiskLevelBadge } from "./risk-level-badge";

type Props = { events: RiskEvent[] };

export function RiskEventTable({ events }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Risk Events</h3>
      </div>
      <div className="divide-y" style={{ borderColor: "var(--border-light)" }}>
        {events.map((evt) => {
          const open = expanded === evt.event_id;
          return (
            <div key={evt.event_id}>
              <button
                onClick={() => setExpanded(open ? null : evt.event_id)}
                className="flex w-full items-center gap-4 px-4 py-3 text-left transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/30"
              >
                <RiskLevelBadge level={evt.risk_level} />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-semibold" style={{ color: "var(--text-primary)" }}>{evt.event_id}</span>
                    {evt.blocked && <span className="rounded-md px-2 py-0.5 text-[10px] font-medium" style={{ background: "var(--success-bg)", color: "var(--success)" }}>Blocked</span>}
                    {!evt.blocked && <span className="rounded-md px-2 py-0.5 text-[10px] font-medium" style={{ background: "var(--warning-bg)", color: "var(--warning)" }}>Monitor</span>}
                  </div>
                  <p className="mt-0.5 text-xs" style={{ color: "var(--text-secondary)" }}>{evt.user_input_excerpt}</p>
                </div>
                <div className="flex flex-wrap gap-1">
                  {evt.risk_tags.slice(0, 2).map((t) => (
                    <span key={t} className="rounded-md px-2 py-0.5 text-[10px]" style={{ background: "var(--bg-subtle)", color: "var(--text-tertiary)" }}>{t}</span>
                  ))}
                </div>
                <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>{new Date(evt.created_at).toLocaleDateString("zh-CN")}</span>
                <span style={{ color: "var(--text-tertiary)" }}>{open ? "▲" : "▼"}</span>
              </button>
              {open && (
                <div className="border-t px-4 py-3" style={{ borderColor: "var(--border-light)", background: "var(--bg-subtle)" }}>
                  <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                    <span className="font-semibold">Reason:</span> {evt.reason}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {evt.risk_tags.map((t) => (
                      <span key={t} className="rounded-md px-2 py-0.5 text-[10px]" style={{ background: "var(--accent-light)", color: "var(--accent)" }}>{t}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
