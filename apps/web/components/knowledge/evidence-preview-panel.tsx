import { StatusBadge } from "@/components/shared/status-badge";
import type { KnowledgeChunk } from "@/lib/mock/knowledge";

type Props = {
  results: KnowledgeChunk[];
  query: string;
};

export function EvidencePreviewPanel({ results, query }: Props) {
  if (!query) {
    return (
      <div className="card">
        <div className="card-header"><h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Evidence Preview</h3></div>
        <div className="card-body text-sm" style={{ color: "var(--text-tertiary)" }}>输入查询关键词后展示检索到的 evidence。</div>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="card">
        <div className="card-header"><h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Evidence Preview</h3></div>
        <div className="card-body text-sm" style={{ color: "var(--text-tertiary)" }}>未找到匹配的 evidence。</div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Evidence Preview</h3>
          <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>Query: &quot;{query}&quot; · {results.length} results</p>
        </div>
      </div>
      <div className="space-y-2 p-3">
        {results.map((chunk) => (
          <div key={chunk.chunk_id} className="rounded-xl border px-4 py-3" style={{ borderColor: "var(--border)", background: "var(--bg-card)" }}>
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{chunk.title}</p>
                  <StatusBadge status="success" label="used_in_answer" />
                </div>
                <p className="mt-0.5 font-mono text-xs" style={{ color: "var(--text-tertiary)" }}>
                  {chunk.chunk_id} · {chunk.source} · score: {chunk.score.toFixed(2)}
                </p>
              </div>
              <span
                className="shrink-0 rounded-full px-2.5 py-0.5 text-xs font-bold"
                style={{
                  background: chunk.score >= 0.9 ? "var(--success-bg)" : chunk.score >= 0.7 ? "var(--warning-bg)" : "var(--bg-subtle)",
                  color: chunk.score >= 0.9 ? "var(--success)" : chunk.score >= 0.7 ? "var(--warning)" : "var(--text-tertiary)",
                }}
              >
                {(chunk.score * 100).toFixed(0)}%
              </span>
            </div>
            <p className="mt-2 text-xs leading-5" style={{ color: "var(--text-secondary)" }}>{chunk.content_excerpt}</p>
            <div className="mt-2 flex flex-wrap gap-1">
              {chunk.keywords.map((kw) => (
                <span key={kw} className="rounded-md px-2 py-0.5 text-[10px] font-medium" style={{ background: "var(--info-bg)", color: "var(--info)" }}>{kw}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
