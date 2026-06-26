import type { ToolResult } from "@/lib/api";

type ToolResultCardProps = {
  toolResult: ToolResult;
};

const statusStyles: Record<string, { label: string; dot: string; border: string; bg: string }> = {
  success: { label: "成功", dot: "bg-emerald-500", border: "border-emerald-200", bg: "bg-emerald-50/20" },
  failed:  { label: "失败", dot: "bg-red-500",    border: "border-red-200",    bg: "bg-red-50/20" },
  error:   { label: "错误", dot: "bg-red-500",    border: "border-red-200",    bg: "bg-red-50/20" },
  skipped: { label: "已跳过", dot: "bg-slate-300", border: "border-slate-200", bg: "bg-slate-50/30" },
  fallback:{ label: "降级",  dot: "bg-amber-400", border: "border-amber-200", bg: "bg-amber-50/20" },
};

function summarize(text: string | undefined, max = 180) {
  if (!text) return "暂无结果";
  return text.length > max ? text.slice(0, max) + "…" : text;
}

export function ToolResultCard({ toolResult }: ToolResultCardProps) {
  const st = toolResult.status || "";
  const style = statusStyles[st] || { label: st, dot: "bg-slate-400", border: "border-slate-200", bg: "bg-slate-50/30" };

  return (
    <div className={`rounded-xl border ${style.border} ${style.bg} p-4`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`inline-block h-2 w-2 rounded-full ${style.dot}`} />
          <h3 className="text-sm font-semibold text-slate-800">
            {toolResult.tool_name || toolResult.tool || "unknown"}
          </h3>
          <span className={`rounded-md px-2 py-0.5 text-xs font-medium ${
            st === "success" ? "bg-emerald-100 text-emerald-700" :
            st === "failed" || st === "error" ? "bg-red-100 text-red-700" :
            st === "fallback" ? "bg-amber-100 text-amber-700" :
            "bg-slate-200 text-slate-500"
          }`}>
            {style.label}
          </span>
        </div>
        {toolResult.latency_ms != null && toolResult.latency_ms > 0 && (
          <span className="text-xs tabular-nums text-slate-400">{toolResult.latency_ms}ms</span>
        )}
      </div>
      <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-400">
        <span>置信度 {toolResult.confidence ?? "-"}</span>
        <span>来源 {toolResult.source || "mock"}</span>
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-700 line-clamp-3">{summarize(toolResult.result)}</p>
    </div>
  );
}
