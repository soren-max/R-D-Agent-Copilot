import type { ToolResult } from "@/lib/api";

type ToolResultCardProps = {
  toolResult: ToolResult;
};

const statusConfig: Record<string, { label: string; dot: string; bg: string }> = {
  success: { label: "成功", dot: "bg-emerald-500", bg: "border-emerald-100 bg-emerald-50/30" },
  failed: { label: "失败", dot: "bg-red-500", bg: "border-red-100 bg-red-50/30" },
  skipped: { label: "已跳过", dot: "bg-slate-400", bg: "border-slate-100 bg-slate-50/50" },
  error: { label: "错误", dot: "bg-red-500", bg: "border-red-100 bg-red-50/30" },
};

function summarize(text: string | undefined, max = 160) {
  if (!text) return "暂无结果";
  return text.length > max ? text.slice(0, max) + "…" : text;
}

export function ToolResultCard({ toolResult }: ToolResultCardProps) {
  const st = toolResult.status || "";
  const cfg = statusConfig[st] || { label: st, dot: "bg-slate-400", bg: "border-slate-100 bg-slate-50/50" };

  return (
    <div className={`rounded-xl border ${cfg.bg} p-4`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`inline-block h-2 w-2 rounded-full ${cfg.dot}`} />
          <h3 className="text-sm font-semibold text-slate-800">
            {toolResult.tool_name || toolResult.tool || "unknown"}
          </h3>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          {toolResult.latency_ms != null && toolResult.latency_ms > 0 && (
            <span>{toolResult.latency_ms}ms</span>
          )}
          <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
            st === "success" ? "bg-emerald-100 text-emerald-700" :
            st === "failed" || st === "error" ? "bg-red-100 text-red-700" :
            "bg-slate-200 text-slate-600"
          }`}>
            {cfg.label}
          </span>
        </div>
      </div>
      <div className="mt-2 flex gap-3 text-xs text-slate-400">
        <span>置信度 {toolResult.confidence ?? "-"}</span>
        <span>来源 {toolResult.source || "mock"}</span>
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-700">{summarize(toolResult.result)}</p>
    </div>
  );
}
