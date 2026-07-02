import type { InjectionAttempt } from "@/lib/mock/safety";

type Props = { injections: InjectionAttempt[] };

export function PromptInjectionPanel({ injections }: Props) {
  return (
    <div className="card">
      <div className="card-header"><h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Prompt Injection Detection</h3></div>
      <div className="divide-y" style={{ borderColor: "var(--border-light)" }}>
        {injections.map((inj, i) => (
          <div key={i} className="px-4 py-3.5">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <pre className="rounded-lg px-3 py-2 text-sm font-mono" style={{ background: "var(--bg-subtle)", color: "var(--text-secondary)" }}>{inj.attack_pattern}</pre>
                <p className="mt-1.5 text-xs leading-5" style={{ color: "var(--text-secondary)" }}>{inj.explanation}</p>
              </div>
              <div className="flex shrink-0 flex-col items-end gap-1.5">
                <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${inj.detected ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}>
                  {inj.detected ? "Detected" : "Missed"}
                </span>
                <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${inj.blocked ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>
                  {inj.blocked ? "Blocked" : "Allowed"}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
