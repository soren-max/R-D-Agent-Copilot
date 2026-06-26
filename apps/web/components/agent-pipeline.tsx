import type { RouteResult, TraceData } from "@/lib/api";

type AgentPipelineProps = {
  route?: RouteResult;
  trace?: TraceData;
  isLoading?: boolean;
};

const stages = [
  { id: "router",      label: "Router 路由器" },
  { id: "planner",     label: "Planner 任务规划" },
  { id: "executor",    label: "LangGraph Executor 执行器" },
  { id: "synthesizer", label: "Answer Synthesizer 回答生成" },
  { id: "evaluation",  label: "Evaluation 质量评估" },
];

type StageStatus = "pending" | "running" | "done";

function stageStatus(id: string, isLoading: boolean, steps: TraceData["steps"]): StageStatus {
  if (!steps || steps.length === 0) return isLoading ? "running" : "pending";
  const found = steps.find((s) => s.stage === id);
  if (found) return "done";
  const order = ["router", "planner", "executor", "synthesizer", "evaluation"];
  const idx = order.indexOf(id);
  const laterDone = order.slice(idx + 1).some((sid) => steps.find((s) => s.stage === sid));
  if (laterDone) return "done";
  return isLoading ? "running" : "pending";
}

function StageDot({ status }: { status: StageStatus }) {
  const colors = { pending: "bg-slate-200", running: "bg-amber-400 animate-pulse", done: "bg-emerald-500" };
  return <span className={`inline-block h-2.5 w-2.5 rounded-full ${colors[status]}`} />;
}

function StageLabel({ status }: { status: StageStatus }) {
  const map = { pending: "等待中", running: "执行中", done: "已完成" };
  const colors = { pending: "text-slate-400", running: "text-amber-600", done: "text-emerald-600" };
  return <span className={`text-xs ${colors[status]}`}>{map[status]}</span>;
}

export function AgentPipeline({ route, trace, isLoading = false }: AgentPipelineProps) {
  const steps = trace?.steps;
  return (
    <div className="card">
      <div className="card-header">
        <h2 className="text-sm font-semibold text-slate-900">Agent Pipeline</h2>
      </div>
      <div className="card-body">
        <div className="space-y-0">
          {stages.map((stage, idx) => {
            const status = stageStatus(stage.id, isLoading, steps);
            return (
              <div key={stage.id} className="relative flex items-start gap-3 pb-4 last:pb-0">
                {idx < stages.length - 1 && (
                  <div className={`absolute left-[11px] top-4 h-full w-px ${status === "done" ? "bg-emerald-200" : "bg-slate-200"}`} />
                )}
                <div className="relative z-10 mt-0.5"><StageDot status={status} /></div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-slate-800">{stage.label}</span>
                    <StageLabel status={status} />
                  </div>
                  {stage.id === "router" && route && (
                    <p className="mt-0.5 text-xs text-slate-400 truncate">
                      {route.type === "simple_qa" ? "简单问答" : "复杂排障"} · {route.confidence}
                    </p>
                  )}
                  {stage.id === "executor" && status === "done" && (
                    <p className="mt-0.5 text-xs text-slate-400">
                      {steps?.find((s) => s.stage === "executor")?.tool_calls?.length ?? 0} 个工具
                    </p>
                  )}
                  {stage.id === "evaluation" && status === "done" && (
                    <p className="mt-0.5 text-xs text-slate-400">
                      {steps?.find((s) => s.stage === "evaluation")?.overall_score != null
                        ? `${Math.round((steps.find((s) => s.stage === "evaluation")!.overall_score!) * 100)}%`
                        : "已评估"}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
