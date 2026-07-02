import { StatusBadge } from "@/components/shared/status-badge";
import type { SystemServiceStatus } from "@/lib/mock/settings";

type Props = { services: SystemServiceStatus };

const labels: Record<keyof SystemServiceStatus, string> = {
  llm_provider: "LLM Provider",
  rag_service: "RAG Service",
  trace_service: "Trace Service",
  evaluation_service: "Evaluation Service",
  safety_guard: "Safety Guard",
};

const statusMap: Record<string, "success" | "warning" | "error"> = {
  healthy: "success", degraded: "warning", unreachable: "error",
};

export function SystemStatusPanel({ services }: Props) {
  return (
    <div className="card">
      <div className="card-header"><h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>System Status</h3></div>
      <div className="card-body grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {(Object.keys(labels) as Array<keyof SystemServiceStatus>).map((key) => (
          <div key={key} className="flex items-center justify-between rounded-xl border px-4 py-3" style={{ borderColor: "var(--border)" }}>
            <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>{labels[key]}</span>
            <StatusBadge status={statusMap[services[key]]} label={services[key]} />
          </div>
        ))}
      </div>
    </div>
  );
}
