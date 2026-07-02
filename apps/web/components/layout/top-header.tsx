"use client";

import { useEffect, useState } from "react";
import type { TraceData, EvaluationResult, ToolResult } from "@/lib/api";

type TopHeaderProps = {
  title: string;
  evaluation?: EvaluationResult | null;
  trace?: TraceData;
  toolResults?: ToolResult[];
};

export function TopHeader({ title, evaluation, trace, toolResults }: TopHeaderProps) {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const cls = document.documentElement.classList;
    setDark(cls.contains("dark"));
  }, []);

  const toggleDark = () => {
    const cls = document.documentElement.classList;
    cls.toggle("dark");
    setDark(cls.contains("dark"));
  };

  const evalScore = evaluation?.overall_score;
  const toolCount = toolResults?.length ?? 0;
  const steps = trace?.steps ?? [];
  const totalLatency = steps.reduce((s, st) => s + (st.latency_ms ?? 0), 0);

  return (
    <header
      className="sticky top-0 z-30 flex h-14 items-center justify-between border-b px-6 backdrop-blur-md"
      style={{
        background: "color-mix(in srgb, var(--bg-card) 85%, transparent)",
        borderColor: "var(--border)",
      }}
    >
      {/* Left: page title + breadcrumb */}
      <div className="flex items-center gap-3">
        <h1 className="text-base font-semibold" style={{ color: "var(--text-primary)" }}>
          {title}
        </h1>
        {steps.length > 0 && (
          <span className="badge-slate text-[11px]">{totalLatency}ms</span>
        )}
      </div>

      {/* Right: status + actions */}
      <div className="flex items-center gap-2.5">
        {evalScore != null && (
          <span className="badge-brand text-[11px]">
            评分 {Math.round(evalScore * 100)}%
          </span>
        )}
        {toolCount > 0 && (
          <span className="badge-slate text-[11px]">{toolCount} tools</span>
        )}
        <span className="badge-success text-[11px]">
          <span className="dot-success" />
          DeepSeek
        </span>
        <span className="badge-slate text-[11px]">
          <span className="dot-success" />
          Healthy
        </span>
        <button
          onClick={toggleDark}
          className="flex h-8 w-8 items-center justify-center rounded-lg text-sm transition-colors"
          style={{
            background: dark ? "var(--bg-subtle)" : "var(--bg-subtle)",
            color: "var(--text-secondary)",
          }}
          title={dark ? "切换亮色模式" : "切换暗色模式"}
        >
          {dark ? "☀" : "☾"}
        </button>
      </div>
    </header>
  );
}
