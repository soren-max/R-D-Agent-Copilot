import type { ChatResponse, RagDocument, RagMetadata, ToolResult } from "@/lib/api";

type RagPanelProps = {
  result?: ChatResponse | null;
};

function findRagResult(toolResults?: ToolResult[]) {
  return toolResults?.find((item) => item.tool === "rag_retriever" || item.tool_name === "rag_retriever");
}

function fallbackValue(value: string | number | undefined | null, empty = "暂无数据") {
  return value === undefined || value === null || value === "" ? empty : value;
}

function scoreLabel(score?: number) {
  if (typeof score !== "number") return "—";
  return score.toFixed(3);
}

function statusLabel(status?: string) {
  if (status === "grounded") return "证据充足";
  if (status === "insufficient_evidence") return "知识库证据不足";
  return status || "暂无数据";
}

function metadataFromTrace(result?: ChatResponse | null): RagMetadata {
  const executor = result?.trace?.steps?.find((step) => step.stage === "executor");
  return {
    retrieval_top_k: executor?.retrieval_top_k ?? undefined,
    score_threshold: executor?.score_threshold ?? undefined,
    retrieved_count: executor?.retrieved_count ?? undefined,
    grounding_status: executor?.grounding_status || undefined,
    retrieval_latency_ms: executor?.retrieval_latency_ms ?? undefined,
  };
}

function DocumentChunk({ document }: { document: RagDocument }) {
  return (
    <article className="rounded-lg border border-slate-100 bg-white p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-xs font-semibold text-slate-900">{fallbackValue(document.source)}</p>
          <p className="mt-0.5 truncate text-[11px] text-slate-400">{fallbackValue(document.section)}</p>
        </div>
        <div className="flex items-center gap-1.5 text-[11px]">
          <span className="rounded-md bg-emerald-50 px-2 py-0.5 font-semibold text-emerald-700">
            {scoreLabel(document.score)}
          </span>
          <span className="rounded-md bg-slate-100 px-2 py-0.5 text-slate-500">
            {fallbackValue(document.retrieval_type)}
          </span>
        </div>
      </div>
      <p className="mt-2 line-clamp-4 text-xs leading-5 text-slate-600">{fallbackValue(document.content)}</p>
      <p className="mt-2 truncate font-mono text-[11px] text-slate-400">{fallbackValue(document.chunk_id)}</p>
    </article>
  );
}

export function RagPanel({ result }: RagPanelProps) {
  const ragResult = findRagResult(result?.tool_results);
  const metadata = ragResult?.rag_metadata || metadataFromTrace(result);
  const documents = ragResult?.documents || [];
  const groundingStatus = metadata.grounding_status || (documents.length > 0 ? "grounded" : "");
  const insufficient = groundingStatus === "insufficient_evidence";

  return (
    <section className="card">
      <div className="card-header">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-slate-950">RAG Panel</h2>
            <p className="mt-1 text-xs text-slate-500">本地知识库 chunk、检索分数和 grounding 状态。</p>
          </div>
          <span className={insufficient ? "badge-amber" : "badge-green"}>{statusLabel(groundingStatus)}</span>
        </div>
      </div>
      <div className="card-body">
        <div className="grid gap-2 text-xs text-slate-500 sm:grid-cols-4">
          <span className="rounded-lg bg-slate-50 px-2 py-1">Top K {fallbackValue(metadata.retrieval_top_k)}</span>
          <span className="rounded-lg bg-slate-50 px-2 py-1">阈值 {fallbackValue(metadata.score_threshold)}</span>
          <span className="rounded-lg bg-slate-50 px-2 py-1">命中 {fallbackValue(metadata.retrieved_count ?? documents.length)}</span>
          <span className="rounded-lg bg-slate-50 px-2 py-1">耗时 {fallbackValue(metadata.retrieval_latency_ms, "0")}ms</span>
        </div>
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          <span className="badge-slate">检索 {fallbackValue(metadata.retrieval_type || documents[0]?.retrieval_type)}</span>
          <span className={metadata.fallback_used ? "badge-amber" : "badge-green"}>
            Fallback {metadata.fallback_used ? "已触发" : "未触发"}
          </span>
        </div>
        {insufficient && (
          <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm font-medium text-amber-800">
            知识库证据不足
          </div>
        )}
        {documents.length > 0 ? (
          <div className="mt-3 grid gap-3">
            {documents.map((document, index) => (
              <DocumentChunk key={document.chunk_id || `${document.source}-${index}`} document={document} />
            ))}
          </div>
        ) : (
          <p className="mt-3 text-sm text-slate-400">暂无知识库 chunk。</p>
        )}
      </div>
    </section>
  );
}
