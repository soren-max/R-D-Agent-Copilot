import type { KnowledgeDocument } from "@/lib/mock/knowledge";

type Props = {
  documents: KnowledgeDocument[];
  selectedId: string | null;
  onSelect: (id: string) => void;
};

export function KnowledgeDocumentList({ documents, selectedId, onSelect }: Props) {
  return (
    <div className="card">
      <div className="card-header flex items-center justify-between">
        <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Documents</h3>
        <span className="rounded-md px-2 py-0.5 text-xs" style={{ background: "var(--bg-subtle)", color: "var(--text-tertiary)" }}>{documents.length}</span>
      </div>
      <div className="space-y-1.5 p-3">
        {documents.map((doc) => {
          const active = doc.document_id === selectedId;
          return (
            <button
              key={doc.document_id}
              onClick={() => onSelect(doc.document_id)}
              className={`w-full rounded-xl border px-4 py-3 text-left transition-all ${
                active
                  ? "border-indigo-300 bg-indigo-50/60 dark:border-indigo-600 dark:bg-indigo-950/30"
                  : "border-transparent hover:border-slate-200 hover:bg-slate-50 dark:hover:border-slate-700 dark:hover:bg-slate-800/30"
              }`}
              style={{ background: active ? undefined : "transparent" }}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{doc.title}</p>
                  <p className="mt-0.5 truncate font-mono text-xs" style={{ color: "var(--text-tertiary)" }}>{doc.filename}</p>
                </div>
                <span className="shrink-0 rounded-md px-2 py-0.5 text-xs font-medium" style={{ background: "var(--accent-light)", color: "var(--accent)" }}>
                  {doc.chunk_count}
                </span>
              </div>
              <p className="mt-1 line-clamp-2 text-xs" style={{ color: "var(--text-secondary)" }}>{doc.description}</p>
              <div className="mt-2 flex flex-wrap gap-1">
                <span className="rounded-md px-2 py-0.5 text-[10px]" style={{ background: "var(--bg-subtle)", color: "var(--text-tertiary)" }}>{doc.category}</span>
                {doc.tags.slice(0, 3).map((t) => (
                  <span key={t} className="rounded-md px-2 py-0.5 text-[10px]" style={{ background: "var(--bg-subtle)", color: "var(--text-tertiary)" }}>{t}</span>
                ))}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
