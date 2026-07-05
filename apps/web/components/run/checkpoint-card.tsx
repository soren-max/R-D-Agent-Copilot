import type { CheckpointData } from "@/lib/api";
import { StatusBadge } from "@/components/shared/status-badge";

type Props = { checkpoint?: CheckpointData | null };
export function CheckpointCard({ checkpoint }: Props) {
  if (!checkpoint) return null;
  return (
    <div className="card">
      <div className="card-header"><h3 className="text-sm font-semibold" style={{color:"var(--text-primary)"}}>Checkpoint</h3></div>
      <div className="card-body space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <StatusBadge status={checkpoint.status === "completed" ? "success" : "warning"} label={checkpoint.status || "—"} />
          <span className="text-xs" style={{color:"var(--text-tertiary)"}}>Updated: {checkpoint.updated_at ? new Date(checkpoint.updated_at).toLocaleString("zh-CN") : "—"}</span>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <p className="text-xs font-medium mb-1" style={{color:"var(--text-tertiary)"}}>Completed Steps</p>
            <div className="flex flex-wrap gap-1">
              {(checkpoint.completed_steps ?? []).map(s => <span key={s} className="rounded-md px-2 py-1 text-xs bg-emerald-50 text-emerald-700">{s}</span>)}
            </div>
          </div>
          <div>
            <p className="text-xs font-medium mb-1" style={{color:"var(--text-tertiary)"}}>Pending Steps</p>
            <div className="flex flex-wrap gap-1">
              {(checkpoint.pending_steps ?? []).map(s => <span key={s} className="rounded-md px-2 py-1 text-xs" style={{background:"var(--bg-subtle)",color:"var(--text-tertiary)"}}>{s}</span>)}
            </div>
          </div>
        </div>
        {checkpoint.last_error && (
          <div className="rounded-lg px-3 py-2 text-xs" style={{color:"var(--error)",background:"var(--error-bg)"}}>Last error: {checkpoint.last_error}</div>
        )}
        <div className="flex gap-2">
          <button className="rounded-lg px-4 py-2 text-xs font-medium text-white" style={{background:"var(--accent)"}} disabled>查看 checkpoint</button>
          <button className="rounded-lg px-4 py-2 text-xs font-medium" style={{border:"1px solid var(--border)",color:"var(--text-secondary)"}} disabled>继续该 Run</button>
        </div>
      </div>
    </div>
  );
}
