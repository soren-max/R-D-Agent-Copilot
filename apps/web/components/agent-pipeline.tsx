import type { RouteResult, TraceData, TraceStep } from "@/lib/api";

type AgentPipelineProps = {
  route?: RouteResult;
  trace?: TraceData;
  isLoading?: boolean;
};

type StageStatus = "pending" | "running" | "done" | "skipped";

const pipelineStages = [
  { id: "router", label: "Router", sub: "路由器" },
  { id: "planner", label: "Planner", sub: "任务规划" },
  { id: "executor", label: "LangGraph Executor", sub: "执行器" },
  { id: "tools", label: "Tools / RAG", sub: "工具与知识库" },
  { id: "synthesizer", label: "Answer Synthesizer", sub: "回答生成" },
  { id: "evaluation", label: "Evaluation", sub: "质量评估" },
];

function resolveStatus(
  stageId: string,
  isLoading: boolean,
  steps?: TraceStep[],
): StageStatus {
  if (!steps || steps.length === 0) {
    return isLoading ? "running" : "pending";
  }

  if (stageId === "tools") {
    const execStep = steps.find((s) => s.stage === "executor");
    if (execStep) return "done";
    return isLoading ? "running" : "pending";
  }

  if (stageId === "evaluation") {
    // Evaluation data may not be present — treat it as done if we have any result
    const hasAnyResult = steps.length > 0;
    return hasAnyResult ? "done" : "pending";
  }

  const step = steps.find((s) => s.stage === stageId);
  if (step) return "done";

  // If a later stage is done, earlier ones are done too
  const stageOrder = ["router", "planner", "executor", "synthesizer"];
  const myIndex = stageOrder.indexOf(stageId);
  const laterDone = stageOrder.slice(myIndex + 1).some((sid) => steps.find((s) => s.stage === sid));
  if (laterDone) return "done";

  return isLoading ? "running" : "pending";
}

function StageDot({ status }: { status: StageStatus }) {
  const colors: Record<StageStatus, string> = {
    pending: "bg-slate-200",
    running: "bg-amber-400 animate-pulse",
    done: "bg-emerald-500",
    skipped: "bg-slate-300",
  };
  return <span className={`inline-block h-2.5 w-2.5 rounded-full ${colors[status]}`} />;
}

function StageLabel({ status }: { status: StageStatus }) {
  const labels: Record<StageStatus, string> = {
    pending: "等待中",
    running: "执行中",
    done: "已完成",
    skipped: "已跳过",
  };
  const colors: Record<StageStatus, string> = {
    pending: "text-slate-400",
    running: "text-amber-600",
    done: "text-emerald-600",
    skipped: "text-slate-400",
  };
  return <span className={`text-xs ${colors[status]}`}>{labels[status]}</span>;
}

export function AgentPipeline({ route, trace, isLoading = false }: AgentPipelineProps) {
  const steps = trace?.steps;

  return (
    <div className="card p-5">
      <h2 className="text-sm font-semibold text-slate-900">Agent Pipeline</h2>
      <div className="mt-4 space-y-0">
        {pipelineStages.map((stage, idx) => {
          const status = resolveStatus(stage.id, isLoading, steps);
          return (
            <div key={stage.id} className="relative flex items-start gap-3 pb-5 last:pb-0">
              {/* Connector line */}
              {idx < pipelineStages.length - 1 && (
                <div
                  className={`absolute left-[9px] top-4 h-full w-px ${
                    status === "done" ? "bg-emerald-200" : "bg-slate-200"
                  }`}
                />
              )}
              {/* Dot */}
              <div className="relative z-10 mt-1">
                <StageDot status={status} />
              </div>
              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-800">{stage.label}</span>
                  <StageLabel status={status} />
                </div>
                <p className="text-xs text-slate-400">{stage.sub}</p>
                {stage.id === "router" && route && (
                  <p className="mt-1 text-xs text-slate-500 truncate">
                    {route.type === "simple_qa" ? "简单问答" : "复杂排障"} · {route.confidence}
                  </p>
                )}
                {stage.id === "executor" && status === "done" && (
                  <p className="mt-1 text-xs text-slate-500">
                    {steps?.find((s) => s.stage === "executor")?.tool_calls?.length ?? 0} tools
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
