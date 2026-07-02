"use client";

import { useState } from "react";

type Props = {
  onSearch: (query: string) => void;
  categories: string[];
  selectedCategory: string;
  onCategoryChange: (cat: string) => void;
};

export function KnowledgeSearchPanel({ onSearch, categories, selectedCategory, onCategoryChange }: Props) {
  const [query, setQuery] = useState("");

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Search Knowledge Base</h3>
      </div>
      <div className="card-body space-y-3">
        <div className="flex gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && onSearch(query)}
            placeholder="例如：port already in use 怎么排查"
            className="flex-1 rounded-xl border px-4 py-2.5 text-sm transition-colors"
            style={{ borderColor: "var(--border)", background: "var(--bg-subtle)", color: "var(--text-primary)" }}
          />
          <button
            onClick={() => onSearch(query)}
            className="rounded-xl px-5 py-2.5 text-sm font-semibold text-white transition-all hover:opacity-90"
            style={{ background: "var(--accent)" }}
          >
            Search
          </button>
        </div>
        <div className="flex flex-wrap gap-1.5">
          <button
            onClick={() => onCategoryChange("")}
            className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
              selectedCategory === "" ? "text-white" : ""
            }`}
            style={{
              background: selectedCategory === "" ? "var(--accent)" : "var(--bg-subtle)",
              color: selectedCategory === "" ? "#fff" : "var(--text-secondary)",
            }}
          >
            All
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => onCategoryChange(cat)}
              className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
                selectedCategory === cat ? "text-white" : ""
              }`}
              style={{
                background: selectedCategory === cat ? "var(--accent)" : "var(--bg-subtle)",
                color: selectedCategory === cat ? "#fff" : "var(--text-secondary)",
              }}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
