import { MetricCard } from "@/components/shared/metric-card";
import { StatusBadge } from "@/components/shared/status-badge";
import type { EnvironmentInfo } from "@/lib/mock/settings";

type Props = { env: EnvironmentInfo };

export function EnvironmentPanel({ env }: Props) {
  const healthMap: Record<string, "success" | "warning" | "error"> = {
    healthy: "success", degraded: "warning", unreachable: "error",
  };

  return (
    <div className="card">
      <div className="card-header"><h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Environment</h3></div>
      <div className="card-body">
        <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard label="Frontend URL" value={env.frontend_url} />
          <MetricCard label="Backend API" value={env.backend_api_base_url} />
          <MetricCard label="Runtime" value={env.runtime} />
          <MetricCard label="Build Mode" value={env.build_mode} />
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <StatusBadge status={healthMap[env.health_status]} label={`API Health: ${env.health_status}`} />
          <StatusBadge status={env.mock_data_enabled ? "warning" : "success"} label={env.mock_data_enabled ? "Mock Data Enabled" : "Live Data"} />
        </div>
      </div>
    </div>
  );
}
