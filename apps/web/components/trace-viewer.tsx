import type { TraceData, TraceSkippedNode, TraceStep, TraceToolCall } from "@/lib/api";

type TraceViewerProps = {
  trace?: TraceData;
  routeType?: string;
};

const stageLabels: Record<string, string> = {
  router: "Router / 路由器",
  planner: "Planner / 任务规划",
  executor: "Executor / LangGraph 执行器",
  synthesizer: "Synthesizer / 回答生成器",
};

function stageColor(stage: string | undefined): string {
  if (stage === "router") return "border-l-emerald-400";
  if (stage === "planner") return "border-l-blue-400";
  if (stage === "executor") return "border-l-amber-400";
  if (stage === "synthesizer") return "border-l-violet-400";
  return "border-l-slate-300";
}

function engineLabel(e: string | undefined) {
  if (e === "deepseek") return "DeepSeek";
  if (e === "langgraph") return "LangGraph";
  if (e === "fallback") return "规则兜底";
  return e || "—";
}

function statusLabel(s: string | undefined) {
  if (s === "success") return "成功";
  if (s === "failed") return "失败";
  if (s === "skipped") return "已跳过";
  return s || "未知";
}

function statusDot(s: string | undefined) {
  if (s === "success") return "bg-emerald-500";
  if (s === "failed") return "bg-red-500";
  if (s === "skipped") return "bg-slate-300";
  return "bg-slate-300";
}

function TimelineStep({ step, index }: { step: TraceStep; index: number }) {
  return (
    <div className={`border-l-2 ${stageColor(step.stage)} pl-4 pb-5 last:pb-0`}>
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-semibold text-slate-800">
          {step.stage ? (stageLabels[step.stage] || step.stage) : "未知阶段"}
        </span>
        <span className="rounded-md bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
          {step.latency_ms ?? 0}ms
        </span>
        {step.engine && (
          <span className="rounded-md bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700">
            {engineLabel(step.engine)}
          </span>
        )}
      </div>
      {step.stage === "executor" && (
        <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-500">
          <span>工具调用: {step.tool_calls?.length ?? 0}</span>
          <span>跳过节点: {step.skipped_nodes?.length ?? 0}</span>
          <span>Fallback: {step.fallback_used ? "已触发" : "未触发"}</span>
        </div>
      )}
      {step.stage === "synthesizer" && (
        <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-500">
          <span>LLM: {step.llm_used ? "是" : "否"}</span>
          {step.llm_error && <span className="text-red-500">错误: {step.llm_error}</span>}
        </div>
      )}
      <p className="mt-2 text-xs leading-5 text-slate-600">{step.output || "暂无输出"}</p>

      {/* Tool calls for executor */}
      {step.tool_calls && step.tool_calls.length > 0 && (
        <div className="mt-3 space-y-1.5">
          {step.tool_calls.map((tc, i) => (
            <ToolCallBadge key={i} call={tc} />
          ))}
        </div>
      )}

      {/* Skipped nodes */}
      {step.skipped_nodes && step.skipped_nodes.length > 0 && (
        <div className="mt-2 space-y-1">
          {step.skipped_nodes.map((sn, i) => (
            <SkippedBadge key={i} node={sn} />
          ))}
        </div>
      )}
    </div>
  );
}

function ToolCallBadge({ call }: { call: TraceToolCall }) {
  return (
    <div className="flex flex-wrap items-center gap-2 rounded-lg border border-slate-100 bg-slate-50/50 px-3 py-2 text-xs">
      <span className={`inline-block h-1.5 w-1.5 rounded-full ${statusDot(call.status)}`} />
      <span className="font-medium text-slate-700">{call.tool_name || "未知工具"}</span>
      <span className="text-slate-400">节点: {call.node || "-"}</span>
      <span className="text-slate-400">重试: {call.retry_count ?? 0}</span>
      <span className="text-slate-400">{call.latency_ms ? `${call.latency_ms}ms` : ""}</span>
      {call.error && <span className="text-red-500">错误: {call.error}</span>}
    </div>
  );
}

function SkippedBadge({ node }: { node: TraceSkippedNode }) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-dashed border-slate-200 bg-slate-50/30 px-3 py-1.5 text-xs text-slate-500">
      <span>已跳过 {node.node || node.tool_name || "未知节点"}</span>
      {node.reason && <span>原因: {node.reason}</span>}
    </div>
  );
}

export function TraceViewer({ trace, routeType }: TraceViewerProps) {
  const steps = trace?.steps || [];

  return (
    <div className="card p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-slate-900">Trace 执行链路</h2>
        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
          <span>ID: {trace?.trace_id || "-"}</span>
          <span className="rounded-full bg-slate-100 px-2 py-0.5">
            {steps.length} 阶段
          </span>
        </div>
      </div>

      {steps.length > 0 ? (
        <div className="mt-4 space-y-1">
          {steps.map((step, i) => (
            <TimelineStep key={`${step.stage}-${i}`} step={step} index={i} />
          ))}
        </div>
      ) : (
        <p className="mt-4 text-sm text-slate-400">暂无 trace 数据。</p>
      )}
    </div>
  );
}
