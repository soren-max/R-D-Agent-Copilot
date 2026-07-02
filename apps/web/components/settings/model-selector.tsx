import { StatusBadge } from "@/components/shared/status-badge";
import type { ModelOption } from "@/lib/mock/settings";

type Props = { models: ModelOption[] };

export function ModelSelector({ models }: Props) {
  return (
    <div className="card">
      <div className="card-header"><h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Available Models</h3></div>
      <div className="grid gap-3 p-3 sm:grid-cols-2">
        {models.map((m) => (
          <div key={m.name} className={`rounded-xl border-2 px-4 py-3.5 transition-all ${m.status === "selected" ? "border-indigo-400 bg-indigo-50/50 dark:border-indigo-600" : "border-slate-200 dark:border-slate-700"}`}>
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold font-mono" style={{ color: "var(--text-primary)" }}>{m.name}</span>
              <StatusBadge status={m.status === "selected" ? "success" : m.status === "available" ? "pending" : "error"} label={m.status === "selected" ? "Selected" : m.status === "available" ? "Available" : "Unavailable"} />
            </div>
            <div className="mt-2 flex flex-wrap items-center gap-2 text-xs" style={{ color: "var(--text-tertiary)" }}>
              <span>{m.provider}</span>
              <span>·</span>
              <span>{(m.context_window / 1000).toFixed(0)}k context</span>
            </div>
            <div className="mt-2 flex flex-wrap gap-1">
              {m.capabilities.map((c) => (
                <span key={c} className="rounded-md px-2 py-0.5 text-[10px]" style={{ background: "var(--accent-light)", color: "var(--accent)" }}>{c}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
