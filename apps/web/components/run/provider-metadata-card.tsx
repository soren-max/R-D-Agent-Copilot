import type { ProviderMetadata } from "@/lib/api";
import { MetricCard } from "@/components/shared/metric-card";

type Props = { metadata?: ProviderMetadata | null };
export function ProviderMetadataCard({ metadata }: Props) {
  if (!metadata) return null;
  return (
    <div className="card">
      <div className="card-header"><h3 className="text-sm font-semibold" style={{color:"var(--text-primary)"}}>Provider Metadata</h3></div>
      <div className="card-body grid gap-3 sm:grid-cols-3">
        <MetricCard label="Prompt Version" value={metadata.prompt_version || "—"} />
        <MetricCard label="Provider" value={metadata.model_provider || "—"} />
        <MetricCard label="Model" value={metadata.model_name || "—"} />
        <MetricCard label="LLM Enabled" value={metadata.llm_enabled ? "Yes" : "No"} />
        <MetricCard label="Fallback Used" value={metadata.fallback_used ? "Yes" : "No"} />
        <MetricCard label="Schema Valid" value={metadata.schema_valid ? "Yes" : "No"} />
        <MetricCard label="Latency" value={metadata.generation_latency_ms != null ? `${metadata.generation_latency_ms}ms` : "—"} />
        <MetricCard label="Timeout" value={metadata.timeout_ms != null ? `${metadata.timeout_ms}ms` : "—"} />
        <MetricCard label="Retry Count" value={metadata.retry_count ?? "—"} />
        <MetricCard label="Provider Status" value={metadata.provider_status || "—"} />
        <MetricCard label="Fallback Provider Used" value={metadata.fallback_provider_used ? "Yes" : "No"} />
        <MetricCard label="Circuit Open" value={metadata.circuit_open ? "Yes" : "No"} />
        <MetricCard label="Prompt Tokens" value={metadata.prompt_tokens?.toLocaleString() ?? "—"} />
        <MetricCard label="Completion Tokens" value={metadata.completion_tokens?.toLocaleString() ?? "—"} />
        <MetricCard label="Total Tokens" value={metadata.total_tokens?.toLocaleString() ?? "—"} />
        <MetricCard label="Daily Token Usage" value={metadata.daily_token_usage?.toLocaleString() ?? "—"} />
        <MetricCard label="Daily Limit Exceeded" value={metadata.daily_token_limit_exceeded ? "Yes" : "No"} />
        {metadata.provider_error_code && <MetricCard label="Error Code" value={metadata.provider_error_code} />}
      </div>
    </div>
  );
}
