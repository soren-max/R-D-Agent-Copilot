import type { ToolResult } from "@/lib/api";
import { ToolResultCard } from "@/components/tool-result-card";

type ToolEvidenceGridProps = {
  toolResults?: ToolResult[];
};

export function ToolEvidenceGrid({ toolResults = [] }: ToolEvidenceGridProps) {
  return (
    <section className="card">
      <div className="card-header">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-slate-950">Tool Evidence</h2>
            <p className="mt-1 text-xs text-slate-500">日志、配置、Git 与知识库证据摘要。</p>
          </div>
          <span className="badge-slate">{toolResults.length} results</span>
        </div>
      </div>
      <div className="card-body">
        {toolResults.length > 0 ? (
          <div className="grid gap-3 md:grid-cols-2">
            {toolResults.map((toolResult, index) => (
              <ToolResultCard key={`${toolResult.tool_name || toolResult.tool}-${index}`} toolResult={toolResult} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-400">暂无数据</p>
        )}
      </div>
    </section>
  );
}
