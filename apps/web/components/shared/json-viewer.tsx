"use client";

import { useState } from "react";

type JsonViewerProps = {
  data: unknown;
  collapsed?: boolean;
  maxHeight?: string;
};

export function JsonViewer({ data, collapsed = true, maxHeight = "400px" }: JsonViewerProps) {
  const [open, setOpen] = useState(!collapsed);
  const formatted = JSON.stringify(data, null, 2);

  return (
    <div className="overflow-hidden rounded-xl border" style={{ borderColor: "var(--border)" }}>
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-2 text-xs font-medium transition-colors"
        style={{
          background: "var(--bg-subtle)",
          color: "var(--text-secondary)",
        }}
      >
        <span>Raw JSON</span>
        <span className="font-mono">{open ? "▼ 收起" : "▶ 展开"}</span>
      </button>
      {open && (
        <pre
          className="overflow-auto p-4 font-mono text-xs leading-relaxed"
          style={{
            maxHeight,
            background: "#0f172a",
            color: "#e2e8f0",
          }}
        >
          {formatted}
        </pre>
      )}
    </div>
  );
}
