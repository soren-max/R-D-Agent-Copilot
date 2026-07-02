import type { UnsafeCommand } from "@/lib/mock/safety";
import { RiskLevelBadge } from "./risk-level-badge";

type Props = { commands: UnsafeCommand[] };

export function UnsafeCommandPanel({ commands }: Props) {
  return (
    <div className="card">
      <div className="card-header"><h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Unsafe Command Detection</h3></div>
      <div className="divide-y" style={{ borderColor: "var(--border-light)" }}>
        {commands.map((cmd, i) => (
          <div key={i} className="px-4 py-3.5">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <pre className="rounded-lg px-3 py-2 text-sm font-mono" style={{ background: "#0f172a", color: "#f87171", overflow: "auto" }}>{cmd.command}</pre>
                <p className="mt-1.5 text-xs" style={{ color: "var(--text-secondary)" }}>{cmd.reason}</p>
                <div className="mt-2 rounded-lg px-3 py-2" style={{ background: "var(--success-bg)" }}>
                  <p className="text-xs font-medium" style={{ color: "var(--success)" }}>Safer alternative:</p>
                  <p className="mt-0.5 text-xs" style={{ color: "var(--text-secondary)" }}>{cmd.safer_alternative}</p>
                </div>
              </div>
              <RiskLevelBadge level={cmd.risk_level} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
