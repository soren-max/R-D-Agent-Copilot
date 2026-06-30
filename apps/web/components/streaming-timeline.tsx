import type { AgentStreamEvent } from "@/lib/api";

type StreamingTimelineProps = {
  events: AgentStreamEvent[];
  isStreaming: boolean;
};

const stageLabels = [
  { key: "router", label: "Router 正在分流" },
  { key: "planner", label: "Planner 正在规划" },
  { key: "executor", label: "LangGraph 正在执行工具节点" },
  { key: "synthesizer", label: "Synthesizer 正在生成回答" },
  { key: "evaluation", label: "Evaluation 正在评估质量" },
];

const eventLabels: Record<string, string> = {
  router_started: "Router 开始分流",
  router_completed: "Router 完成分流",
  planner_started: "Planner 开始规划",
  planner_completed: "Planner 完成规划",
  executor_started: "LangGraph 开始执行",
  tool_started: "工具开始执行",
  tool_completed: "工具执行完成",
  synthesizer_started: "Synthesizer 开始生成",
  synthesizer_completed: "Synthesizer 完成回答",
  evaluation_started: "Evaluation 开始评估",
  evaluation_completed: "Evaluation 完成评估",
  completed: "Agent 执行完成",
  error: "流式执行失败",
};

function stageStatus(events: AgentStreamEvent[], key: string) {
  const hasFailed = events.some((item) => item.event === "error" || (key === "executor" && item.status === "failed"));
  if (hasFailed) return "failed";
  if (key === "executor" && events.some((item) => item.event === "synthesizer_started" || item.event === "completed")) {
    return "completed";
  }
  if (events.some((item) => item.event === `${key}_completed`)) return "completed";
  if (events.some((item) => item.event === `${key}_started` || (key === "executor" && item.event === "tool_started"))) {
    return "running";
  }
  return "pending";
}

function statusClass(status: string) {
  if (status === "completed") return "border-emerald-200 bg-emerald-50 text-emerald-700";
  if (status === "running") return "border-sky-200 bg-sky-50 text-sky-700";
  if (status === "failed") return "border-red-200 bg-red-50 text-red-700";
  return "border-slate-200 bg-white text-slate-400";
}

function statusText(status: string) {
  if (status === "completed") return "已完成";
  if (status === "running") return "执行中";
  if (status === "failed") return "失败";
  return "等待中";
}

function formatTime(value?: string) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString("zh-CN", { hour12: false });
}

export function StreamingTimeline({ events, isStreaming }: StreamingTimelineProps) {
  if (!isStreaming && events.length === 0) return null;

  return (
    <section className="card">
      <div className="card-header">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-slate-950">实时执行流</h2>
            <p className="mt-1 text-xs text-slate-500">展示 Agent 各阶段执行状态，非 LLM 逐字输出。</p>
          </div>
          <span className={isStreaming ? "badge-blue" : "badge-green"}>{isStreaming ? "执行中" : "已完成"}</span>
        </div>
      </div>
      <div className="card-body space-y-4">
        <div className="grid gap-2 md:grid-cols-5">
          {stageLabels.map((stage) => {
            const status = stageStatus(events, stage.key);
            return (
              <div key={stage.key} className={`rounded-2xl border px-3 py-3 ${statusClass(status)}`}>
                <div className="text-xs font-semibold">{stage.label}</div>
                <div className="mt-1 text-xs opacity-80">{statusText(status)}</div>
              </div>
            );
          })}
        </div>

        <div className="space-y-2">
          {events.map((event, index) => (
            <div key={`${event.event}-${index}`} className="flex gap-3 rounded-2xl border border-slate-100 bg-slate-50/70 px-3 py-2.5">
              <div className={event.event === "error" || event.status === "failed" ? "dot-red mt-1.5" : "dot-green mt-1.5"} />
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-sm font-semibold text-slate-800">{eventLabels[event.event] || event.event}</span>
                  <span className="text-xs tabular-nums text-slate-400">{formatTime(event.timestamp)}</span>
                </div>
                <p className="mt-1 text-xs leading-5 text-slate-500">
                  {event.message || "状态已更新"}
                  {event.tool_name ? ` · ${event.tool_name}` : ""}
                  {typeof event.latency_ms === "number" ? ` · ${event.latency_ms}ms` : ""}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
