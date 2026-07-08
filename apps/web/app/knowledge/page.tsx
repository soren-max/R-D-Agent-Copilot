"use client";

import { useState, useMemo } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { KnowledgeSummaryCards } from "@/components/knowledge/knowledge-summary-cards";
import { KnowledgeSearchPanel } from "@/components/knowledge/knowledge-search-panel";
import { KnowledgeDocumentList } from "@/components/knowledge/knowledge-document-list";
import { ChunkList } from "@/components/knowledge/chunk-list";
import { EvidencePreviewPanel } from "@/components/knowledge/evidence-preview-panel";
import { StatusBadge } from "@/components/shared/status-badge";
import { EmptyState } from "@/components/shared/empty-state";
import {
  mockKnowledgeStats,
  mockDocuments,
  mockChunks,
  mockSearchResults,
} from "@/lib/mock/knowledge";

export default function KnowledgePage() {
  const [selectedDocId, setSelectedDocId] = useState<string>(mockDocuments[0]?.document_id ?? "");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<typeof mockSearchResults>([]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  const filteredDocuments = useMemo(() => {
    if (!selectedCategory) return mockDocuments;
    return mockDocuments.filter((d) => d.category === selectedCategory);
  }, [selectedCategory]);

  const selectedDoc = mockDocuments.find((d) => d.document_id === selectedDocId);
  const chunks = selectedDocId ? mockChunks[selectedDocId] ?? [] : [];

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setHasSearched(true);
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }
    // Simulate search: filter mock results by keyword match
    const q = query.toLowerCase();
    const results = mockSearchResults.filter(
      (r) =>
        r.title.toLowerCase().includes(q) ||
        r.keywords.some((kw) => kw.toLowerCase().includes(q)) ||
        r.content_excerpt.toLowerCase().includes(q),
    );
    setSearchResults(results);
  };

  return (
    <AppShell title="Knowledge Base">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>知识库管理</h2>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            RAG Pipeline — 文档入库 → Chunk 切分 → Hybrid 检索 → Grounding 校验。
          </p>
        </div>
        <StatusBadge status="success" label="Mock Data" />
      </div>

      {/* RAG Pipeline Overview */}
      <div className="card mb-5">
        <div className="card-header">
          <h3 className="text-sm font-semibold" style={{color:"var(--text-primary)"}}>RAG Pipeline</h3>
        </div>
        <div className="card-body">
          <div className="flex items-center gap-0">
            {[
              {label:"Docs",desc:"Markdown 入库",color:"#6366f1"},
              {label:"Chunk",desc:"标题/段落切分",color:"#0284c7"},
              {label:"Metadata",desc:"source/section/doc_type",color:"#059669"},
              {label:"Hybrid",desc:"keyword+vector",color:"#d97706"},
              {label:"ReRank",desc:"分数重排序",color:"#8b5cf6"},
              {label:"Grounding",desc:"证据校验",color:"#0f172a"},
            ].map((s,i)=>(
              <div key={s.label} className="flex items-center gap-0 flex-1">
                <div className="flex flex-col items-center min-w-0">
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-white" style={{background:s.color}}>{i+1}</div>
                  <span className="mt-1 text-[10px] font-semibold text-center" style={{color:"var(--text-secondary)"}}>{s.label}</span>
                  <span className="text-[9px] text-center" style={{color:"var(--text-tertiary)"}}>{s.desc}</span>
                </div>
                {i<5 && <div className="flex-1 h-px mx-1 mb-5" style={{background:"var(--border)"}} />}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="mb-5">
        <KnowledgeSummaryCards stats={mockKnowledgeStats} />
      </div>

      {/* Search + Filters */}
      <div className="mb-5">
        <KnowledgeSearchPanel
          onSearch={handleSearch}
          categories={mockKnowledgeStats.categories}
          selectedCategory={selectedCategory}
          onCategoryChange={setSelectedCategory}
        />
      </div>

      {/* Main area: doc list + detail */}
      <div className="grid gap-5 lg:grid-cols-[360px_minmax(0,1fr)]">
        {/* Document List */}
        <KnowledgeDocumentList
          documents={filteredDocuments}
          selectedId={selectedDocId}
          onSelect={setSelectedDocId}
        />

        {/* Detail area */}
        <div className="min-w-0 space-y-4">
          {searchQuery && hasSearched ? (
            <EvidencePreviewPanel results={searchResults} query={searchQuery} />
          ) : selectedDoc ? (
            <>
              {/* Document header */}
              <div className="card">
                <div className="card-header">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{selectedDoc.title}</h3>
                      <p className="mt-0.5 font-mono text-xs" style={{ color: "var(--text-tertiary)" }}>{selectedDoc.filename}</p>
                    </div>
                    <span className="shrink-0 rounded-full px-3 py-1 text-xs font-medium" style={{ background: "var(--success-bg)", color: "var(--success)" }}>
                      {selectedDoc.status}
                    </span>
                  </div>
                  <p className="mt-2 text-sm" style={{ color: "var(--text-secondary)" }}>{selectedDoc.description}</p>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    <span className="rounded-md px-2.5 py-1 text-xs font-medium" style={{ background: "var(--accent-light)", color: "var(--accent)" }}>
                      {selectedDoc.category}
                    </span>
                    {selectedDoc.tags.map((t) => (
                      <span key={t} className="rounded-md px-2.5 py-1 text-xs" style={{ background: "var(--bg-subtle)", color: "var(--text-tertiary)" }}>
                        {t}
                      </span>
                    ))}
                    <span className="rounded-md px-2.5 py-1 text-xs" style={{ background: "var(--bg-subtle)", color: "var(--text-tertiary)" }}>
                      {selectedDoc.chunk_count} chunks
                    </span>
                    <span className="rounded-md px-2.5 py-1 text-xs" style={{ background: "var(--bg-subtle)", color: "var(--text-tertiary)" }}>
                      更新于 {selectedDoc.updated_at}
                    </span>
                  </div>
                </div>
              </div>

              {/* Chunks */}
              <ChunkList chunks={chunks} title={`Chunks (${selectedDoc.filename})`} />
            </>
          ) : (
            <EmptyState title="选择文档" description="从左侧列表选择一个文档查看 chunks。" />
          )}
        </div>
      </div>
    </AppShell>
  );
}
