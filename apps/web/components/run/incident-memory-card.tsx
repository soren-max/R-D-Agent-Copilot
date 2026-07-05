import type { IncidentMemory } from "@/lib/api";

type Props = { memory?: IncidentMemory | null };
export function IncidentMemoryCard({ memory }: Props) {
  if (!memory) return null;
  return (
    <div className="card">
      <div className="card-header"><h3 className="text-sm font-semibold" style={{color:"var(--text-primary)"}}>Incident Memory</h3></div>
      <div className="card-body space-y-4">
        <div className="flex flex-wrap gap-3 text-xs" style={{color:"var(--text-tertiary)"}}>
          <span>Total hits: <strong style={{color:"var(--text-primary)"}}>{memory.memory_hit_count}</strong></span>
          <span className="dot-success" /> Fresh: {memory.fresh_count ?? 0}
          <span className="dot-warning" /> Weak: {memory.weak_count ?? 0}
          <span className="dot-error" /> Stale: {memory.stale_count ?? 0}
        </div>
        {memory.entries && memory.entries.length > 0 && (
          <div className="space-y-2">
            {memory.entries.map((e,i) => (
              <div key={i} className="rounded-xl border px-4 py-3" style={{borderColor:"var(--border)"}}>
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-semibold truncate" style={{color:"var(--text-primary)"}}>{e.query || "—"}</p>
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    e.freshness_status === "fresh" ? "bg-emerald-50 text-emerald-700" :
                    e.freshness_status === "weak" ? "bg-amber-50 text-amber-700" :
                    "bg-slate-100 text-slate-500"
                  }`}>{e.freshness_status}</span>
                </div>
                <p className="mt-1 text-xs" style={{color:"var(--text-tertiary)"}}>Match: {e.match_reason || "—"} · Run: {e.run_id ? e.run_id.slice(0,8)+"…" : "—"}</p>
              </div>
            ))}
          </div>
        )}
        <div className="rounded-xl border px-4 py-3" style={{borderColor:"var(--warning-bg)",background:"var(--warning-bg)"}}>
          <p className="text-xs font-medium" style={{color:"var(--warning)"}}>⚠ Incident Memory 是历史参考，不能作为当前证据。</p>
        </div>
      </div>
    </div>
  );
}
