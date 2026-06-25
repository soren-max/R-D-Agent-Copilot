import type { ToolResult } from "@/lib/api";

type ToolResultCardProps = {
  toolResult: ToolResult;
};

function statusLabel(status: string | undefined) {
  if (status === "success") {
    return "成功";
  }
  if (status === "failed") {
    return "失败";
  }
  if (status === "skipped") {
    return "已跳过";
  }
  return status || "未知状态";
}

function summarize(text: string | undefined) {
  if (!text) {
    return "暂无结果摘要";
  }
  return text.length > 140 ? `${text.slice(0, 140)}...` : text;
}

export function ToolResultCard({ toolResult }: ToolResultCardProps) {
  return (
    <article className="rounded-md border border-slate-200 bg-slate-50 p-4">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-sm font-semibold text-slate-950">
          {toolResult.tool_name || toolResult.tool || "unknown_tool"}
        </h3>
        <span className="rounded-full bg-white px-2 py-1 text-xs text-slate-600">
          {statusLabel(toolResult.status)}
        </span>
      </div>
      <dl className="mt-3 space-y-1 text-xs text-slate-600">
        <div>置信度：{toolResult.confidence}</div>
        <div>来源：{toolResult.source || "无"}</div>
      </dl>
      <p className="mt-3 text-sm leading-6 text-slate-800">{summarize(toolResult.result)}</p>
    </article>
  );
}
