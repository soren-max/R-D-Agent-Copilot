import type { EvidenceChain, EvidenceItem } from "@/lib/api";

type EvidencePanelProps = {
  evidenceChain?: EvidenceChain | null;
};

const typeLabels: Record<string, string> = {
  log: "日志",
  config: "配置",
  git: "Git",
  rag: "知识库",
  evaluation: "评估",
};

const typeBadges: Record<string, string> = {
  log: "badge-red",
  config: "badge-blue",
  git: "badge-amber",
  rag: "badge-green",
  evaluation: "badge-slate",
};

function toPercent(value: number | undefined) {
  if (typeof value !== "number" || Number.isNaN(value)) return "—";
  return `${Math.round(Math.max(0, Math.min(1, value)) * 100)}%`;
}

function evidenceLabel(item: EvidenceItem) {
  return typeLabels[item.type] ?? item.type;
}

export function EvidencePanel({ evidenceChain }: EvidencePanelProps) {
  if (!evidenceChain) {
    return (
      <section className="card">
        <div className="card-header">
          <h2 className="text-base font-semibold text-slate-950">证据链与置信度</h2>
        </div>
        <div className="card-body">
          <p className="text-sm text-slate-400">暂无证据链</p>
        </div>
      </section>
    );
  }

  const candidates = evidenceChain.root_cause_candidates || [];
  const evidenceItems = evidenceChain.evidence_items || [];
  const evidenceById = new Map(evidenceItems.map((item) => [item.id, item]));

  return (
    <section className="card">
      <div className="card-header">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-slate-950">证据链与置信度</h2>
            <p className="mt-1 text-xs text-slate-500">基于工具结果、知识库与评估结果的 rule-based 解释。</p>
          </div>
          <div className="rounded-2xl border border-emerald-100 bg-emerald-50 px-4 py-2 text-right">
            <span className="block text-2xl font-bold tabular-nums text-emerald-700">
              {toPercent(evidenceChain.overall_confidence)}
            </span>
            <span className="text-xs font-semibold text-emerald-700">根因置信度</span>
          </div>
        </div>
      </div>

      <div className="card-body space-y-5">
        <div>
          <div className="mb-2 flex items-center justify-between gap-3">
            <h3 className="text-xs font-semibold text-slate-700">可能原因</h3>
            <span className="badge-slate">{candidates.length} candidates</span>
          </div>
          {candidates.length > 0 ? (
            <div className="space-y-3">
              {candidates.map((candidate) => {
                const pct = Math.round(Math.max(0, Math.min(1, candidate.confidence)) * 100);
                return (
                  <article key={candidate.title} className="rounded-2xl border border-slate-100 bg-slate-50/70 p-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <h4 className="max-w-2xl text-sm font-semibold leading-6 text-slate-900">{candidate.title}</h4>
                      <span className="badge-green tabular-nums">{toPercent(candidate.confidence)}</span>
                    </div>
                    <div className="mt-3 h-1.5 w-full rounded-full bg-white">
                      <div className="h-1.5 rounded-full bg-emerald-500" style={{ width: `${pct}%` }} />
                    </div>
                    <p className="mt-3 text-sm leading-6 text-slate-600">{candidate.reason}</p>
                    {(candidate.supporting_evidence_ids || []).length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {(candidate.supporting_evidence_ids || []).map((id) => {
                          const item = evidenceById.get(id);
                          return (
                            <span key={id} className="badge-slate">
                              {item ? `${evidenceLabel(item)} · ${id}` : id}
                            </span>
                          );
                        })}
                      </div>
                    )}
                  </article>
                );
              })}
            </div>
          ) : (
            <p className="rounded-2xl border border-slate-100 bg-slate-50/70 px-4 py-3 text-sm text-slate-400">
              暂无可确认的根因候选。
            </p>
          )}
        </div>

        <div>
          <div className="mb-2 flex items-center justify-between gap-3">
            <h3 className="text-xs font-semibold text-slate-700">证据列表</h3>
            <span className="badge-slate">{evidenceItems.length} evidence</span>
          </div>
          {evidenceItems.length > 0 ? (
            <div className="grid gap-3 md:grid-cols-2">
              {evidenceItems.map((item) => {
                const pct = Math.round(Math.max(0, Math.min(1, item.confidence)) * 100);
                return (
                  <article key={item.id} className="rounded-2xl border border-slate-100 bg-white p-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className={typeBadges[item.type] || "badge-slate"}>{evidenceLabel(item)}</span>
                      <span className="text-xs font-semibold tabular-nums text-slate-600">{toPercent(item.confidence)}</span>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-slate-700">{item.summary}</p>
                    <dl className="mt-3 space-y-1 text-xs text-slate-500">
                      <div className="flex gap-2">
                        <dt className="shrink-0 font-medium text-slate-600">来源</dt>
                        <dd className="min-w-0 break-words">{item.source || "未提供"}</dd>
                      </div>
                      <div className="flex gap-2">
                        <dt className="shrink-0 font-medium text-slate-600">工具</dt>
                        <dd>{item.related_tool || "unknown"}</dd>
                      </div>
                    </dl>
                    <div className="mt-3 h-1.5 w-full rounded-full bg-slate-100">
                      <div className="h-1.5 rounded-full bg-sky-500" style={{ width: `${pct}%` }} />
                    </div>
                  </article>
                );
              })}
            </div>
          ) : (
            <p className="rounded-2xl border border-slate-100 bg-slate-50/70 px-4 py-3 text-sm text-slate-400">
              暂无证据项。
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
