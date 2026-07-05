import type { ContextMetadata } from "@/lib/api";
import { MetricCard } from "@/components/shared/metric-card";

type Props = { metadata?: ContextMetadata | null };
export function ContextMetadataCard({ metadata }: Props) {
  if (!metadata) return null;
  const ratio = metadata.compression_ratio != null ? `${(metadata.compression_ratio * 100).toFixed(0)}%` : "—";
  return (
    <div className="card">
      <div className="card-header"><h3 className="text-sm font-semibold" style={{color:"var(--text-primary)"}}>Context Metadata</h3></div>
      <div className="card-body grid gap-3 sm:grid-cols-3">
        <MetricCard label="Before (chars)" value={metadata.total_chars_before?.toLocaleString() ?? "—"} />
        <MetricCard label="After (chars)" value={metadata.total_chars_after?.toLocaleString() ?? "—"} />
        <MetricCard label="Compression" value={ratio} />
        <MetricCard label="Reduced Sections" value={metadata.reduced_sections ?? "—"} />
        <MetricCard label="Query Preserved" value={metadata.current_query_preserved ? "Yes" : "No"} />
        <MetricCard label="Memory Hits" value={metadata.memory_hit_count ?? 0} />
      </div>
    </div>
  );
}
