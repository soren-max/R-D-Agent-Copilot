import type { SafetyPolicy } from "@/lib/mock/safety";
import { RiskLevelBadge } from "./risk-level-badge";

type Props = { policy: SafetyPolicy };

export function SafetyPolicyCard({ policy }: Props) {
  return (
    <div className="card px-4 py-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{policy.policy_name}</span>
            <span
              className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium"
              style={{
                background: policy.status === "enabled" ? "var(--success-bg)" : "var(--bg-subtle)",
                color: policy.status === "enabled" ? "var(--success)" : "var(--text-tertiary)",
              }}
            >
              <span className={`inline-block h-1.5 w-1.5 rounded-full ${policy.status === "enabled" ? "bg-emerald-500" : "bg-slate-300"}`} />
              {policy.status === "enabled" ? "Enabled" : "Disabled"}
            </span>
            <RiskLevelBadge level={policy.severity} />
          </div>
          <p className="mt-1.5 text-xs leading-5" style={{ color: "var(--text-secondary)" }}>{policy.description}</p>
        </div>
      </div>
      {policy.last_triggered_at && (
        <p className="mt-2 text-xs" style={{ color: "var(--text-tertiary)" }}>
          Last triggered: {new Date(policy.last_triggered_at).toLocaleString("zh-CN")}
        </p>
      )}
    </div>
  );
}
