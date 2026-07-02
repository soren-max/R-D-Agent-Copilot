import { MetricCard } from "@/components/shared/metric-card";
import type { SafetyStats } from "@/lib/mock/safety";

type Props = { stats: SafetyStats };

export function SafetySummaryCards({ stats }: Props) {
  return (
    <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
      <MetricCard label="Total Risk Events" value={stats.total_risk_events} />
      <MetricCard label="Blocked Actions" value={stats.blocked_actions} secondary={`${Math.round((stats.blocked_actions / stats.total_risk_events) * 100)}% blocked`} />
      <MetricCard label="Injection Attempts" value={stats.injection_attempts} />
      <MetricCard label="Secrets Masked" value={stats.secret_masked_count} />
      <MetricCard label="Unsafe Alerts" value={stats.unsafe_command_alerts} />
      <div className="card px-4 py-3.5">
        <p className="text-xs font-medium" style={{ color: "var(--text-tertiary)" }}>Safety Score</p>
        <div className="mt-1 flex items-center gap-2">
          <span className="metric-value" style={{ color: stats.safety_score >= 0.9 ? "var(--success)" : stats.safety_score >= 0.7 ? "var(--warning)" : "var(--error)" }}>
            {Math.round(stats.safety_score * 100)}%
          </span>
          <span className="text-xs font-medium" style={{ color: "var(--text-tertiary)" }}>
            {stats.safety_score >= 0.9 ? "Excellent" : stats.safety_score >= 0.7 ? "Good" : "Needs Improvement"}
          </span>
        </div>
      </div>
    </div>
  );
}
