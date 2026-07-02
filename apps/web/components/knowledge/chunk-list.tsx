import { ScoreBar } from "@/components/shared/score-bar";
import type { KnowledgeChunk } from "@/lib/mock/knowledge";

type Props = {
  chunks: KnowledgeChunk[];
  title: string;
};

export function ChunkList({ chunks, title }: Props) {
  if (chunks.length === 0) {
    return (
      <div className="card">
        <div className="card-header"><h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{title}</h3></div>
        <div className="card-body text-sm" style={{ color: "var(--text-tertiary)" }}>暂无 chunks。</div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header flex items-center justify-between">
        <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{title}</h3>
        <span className="rounded-md px-2 py-0.5 text-xs" style={{ background: "var(--bg-subtle)", color: "var(--text-tertiary)" }}>{chunks.length}</span>
      </div>
      <div className="space-y-2 p-3">
        {chunks.map((chunk) => (
          <div key={chunk.chunk_id} className="rounded-xl border px-4 py-3" style={{ borderColor: "var(--border)", background: "var(--bg-card)" }}>
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{chunk.title}</p>
                <p className="mt-0.5 font-mono text-xs" style={{ color: "var(--text-tertiary)" }}>{chunk.chunk_id} · {chunk.source}</p>
              </div>
              <div className="w-16 shrink-0">
                <ScoreBar value={Math.round(chunk.score * 100)} size="sm" showValue />
              </div>
            </div>
            <p className="mt-2 text-xs leading-5" style={{ color: "var(--text-secondary)" }}>{chunk.content_excerpt}</p>
            <div className="mt-2 flex flex-wrap gap-1">
              <span className="rounded-md px-2 py-0.5 text-[10px]" style={{ background: "var(--accent-light)", color: "var(--accent)" }}>{chunk.category}</span>
              {chunk.keywords.map((kw) => (
                <span key={kw} className="rounded-md px-2 py-0.5 text-[10px]" style={{ background: "var(--bg-subtle)", color: "var(--text-tertiary)" }}>{kw}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
