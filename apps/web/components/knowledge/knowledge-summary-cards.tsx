import { MetricCard } from "@/components/shared/metric-card";
import type { KnowledgeBaseStats } from "@/lib/mock/knowledge";

type Props = { stats: KnowledgeBaseStats };

export function KnowledgeSummaryCards({ stats }: Props) {
  const statusColors: Record<string, { dot: string; label: string }> = {
    healthy: { dot: "var(--success)", label: "Healthy" },
    degraded: { dot: "var(--warning)", label: "Degraded" },
    building: { dot: "var(--accent)", label: "Building" },
  };
  const s = statusColors[stats.kb_status] || statusColors.healthy;

  return (
    <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
      <MetricCard label="Total Documents" value={stats.total_documents} />
      <MetricCard label="Total Chunks" value={stats.total_chunks} />
      <MetricCard label="Categories" value={stats.categories.length} />
      <div className="card px-4 py-3.5">
        <p className="text-xs font-medium" style={{ color: "var(--text-tertiary)" }}>Retrieval Strategy</p>
        <p className="mt-1 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{stats.retrieval_strategy}</p>
      </div>
      <div className="card px-4 py-3.5">
        <p className="text-xs font-medium" style={{ color: "var(--text-tertiary)" }}>Last Indexed</p>
        <p className="mt-1 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{new Date(stats.last_indexed).toLocaleDateString("zh-CN")}</p>
      </div>
      <div className="card px-4 py-3.5">
        <p className="text-xs font-medium" style={{ color: "var(--text-tertiary)" }}>KB Status</p>
        <div className="mt-1 flex items-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: s.dot }} />
          <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{s.label}</span>
        </div>
      </div>
    </div>
  );
}
