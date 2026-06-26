import type { TraceData, TraceSkippedNode, TraceStep, TraceToolCall } from "@/lib/api";

type TraceViewerProps = {
  trace?: TraceData;
  routeType?: string;
};

const stageLabels: Record<string, { en: string; zh: string }> = {
  router: { en: "Router", zh: "路由器" },
  planner: { en: "Planner", zh: "任务规划" },
  executor: { en: "Executor", zh: "执行器" },
  synthesizer: { en: "Synthesizer", zh: "回答生成器" },
  evaluation: { en: "Evaluation", zh: "质量评估" },
};

function stageLabel(stage: string | undefined) {
  if (!stage) {
    return "未知阶段";
  }
  const label = stageLabels[stage];
  return label ? `${label.en} / ${label.zh}` : stage;
}

function routeLabel(routeType: string | undefined) {
  if (routeType === "simple_qa") {
    return "simple_qa / 简单问答";
  }
  if (routeType === "complex_troubleshooting") {
    return "complex_troubleshooting / 复杂排障";
  }
  return routeType || "未知类型";
}

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

function engineLabel(engine: string | undefined) {
  if (engine === "deepseek") {
    return "DeepSeek";
  }
  if (engine === "fallback") {
    return "规则兜底";
  }
  if (engine === "langgraph") {
    return "LangGraph";
  }
  if (engine === "rule_based") {
    return "规则评估";
  }
  return engine || "未记录";
}

function reasonLabel(reason: string | undefined) {
  if (reason === "tool_not_in_plan") {
    return "工具不在计划中";
  }
  return reason || "未记录原因";
}

function findStep(trace: TraceData | undefined, stage: string) {
  return trace?.steps?.find((step) => step.stage === stage);
}

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-2 break-words text-sm font-semibold text-slate-950">{value}</p>
    </div>
  );
}

function TimelineStep({ step, index }: { step: TraceStep; index: number }) {
  return (
    <article className="relative rounded-md border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-700 text-xs font-semibold text-white">
          {index + 1}
        </span>
        <h3 className="text-sm font-semibold text-slate-950">{stageLabel(step.stage)}</h3>
        <span className="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-600">
          耗时：{step.latency_ms ?? 0} ms
        </span>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-700">{step.output || "暂无阶段输出"}</p>
    </article>
  );
}

function ToolCallItem({ call }: { call: TraceToolCall }) {
  return (
    <article className="rounded-md border border-slate-200 bg-slate-50 p-3">
      <div className="flex flex-wrap gap-2 text-xs text-slate-600">
        <span>节点：{call.node || "未记录"}</span>
        <span>工具：{call.tool_name || "未记录"}</span>
        <span>状态：{statusLabel(call.status)}</span>
      </div>
      <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-600">
        <span>耗时：{call.latency_ms ?? 0} ms</span>
        <span>重试：{call.retry_count ?? 0}</span>
        <span>来源：{call.source || "无"}</span>
      </div>
      {call.error ? <p className="mt-2 text-xs text-red-700">错误：{call.error}</p> : null}
    </article>
  );
}

function SkippedNodeItem({ node }: { node: TraceSkippedNode }) {
  return (
    <article className="rounded-md border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
      <div>节点：{node.node || "未记录"}</div>
      <div className="mt-1">工具：{node.tool_name || "未记录"}</div>
      <div className="mt-1">原因：{reasonLabel(node.reason)}</div>
    </article>
  );
}

function ExecutorPanel({ step }: { step?: TraceStep }) {
  if (!step) {
    return (
      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-950">LangGraph 执行器</h2>
        <p className="mt-3 text-sm text-slate-600">暂无执行器 trace。</p>
      </section>
    );
  }

  const toolCalls = step.tool_calls || [];
  const skippedNodes = step.skipped_nodes || [];

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="text-lg font-semibold text-slate-950">LangGraph 执行器</h2>
        <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
          {engineLabel(step.engine)}
        </span>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">
          fallback：{step.fallback_used ? "已触发" : "未触发"}
        </span>
      </div>
      <p className="mt-3 text-sm text-slate-700">执行图：{step.graph_name || "未记录"}</p>

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <div>
          <h3 className="text-sm font-semibold text-slate-950">工具调用</h3>
          <div className="mt-3 grid gap-3">
            {toolCalls.length > 0 ? (
              toolCalls.map((call, index) => <ToolCallItem key={`${call.node}-${index}`} call={call} />)
            ) : (
              <p className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600">
                暂无工具调用。
              </p>
            )}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-slate-950">跳过节点</h3>
          <div className="mt-3 grid gap-3">
            {skippedNodes.length > 0 ? (
              skippedNodes.map((node, index) => (
                <SkippedNodeItem key={`${node.node}-${index}`} node={node} />
              ))
            ) : (
              <p className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600">
                没有跳过节点。
              </p>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

function SynthesizerPanel({ step }: { step?: TraceStep }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-950">回答生成器</h2>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="引擎" value={engineLabel(step?.engine)} />
        <MetricCard label="是否使用 LLM" value={step?.llm_used ? "是" : "否"} />
        <MetricCard label="LLM 错误" value={step?.llm_error || "无"} />
        <MetricCard label="耗时" value={`${step?.latency_ms ?? 0} ms`} />
      </div>
    </section>
  );
}

function EvaluationTracePanel({ step }: { step?: TraceStep }) {
  if (!step) {
    return null;
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-950">质量评估 Trace</h2>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <MetricCard label="引擎" value={engineLabel(step.engine)} />
        <MetricCard
          label="总体评分"
          value={
            typeof step.overall_score === "number"
              ? `${Math.round(step.overall_score * 100)}%`
              : "未记录"
          }
        />
        <MetricCard label="耗时" value={`${step.latency_ms ?? 0} ms`} />
      </div>
    </section>
  );
}

export function TraceViewer({ trace, routeType }: TraceViewerProps) {
  const steps = trace?.steps || [];
  const executorStep = findStep(trace, "executor");
  const synthesizerStep = findStep(trace, "synthesizer");
  const evaluationStep = findStep(trace, "evaluation");
  const usesLangGraph = executorStep?.engine === "langgraph";

  return (
    <section className="grid gap-5">
      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-950">Trace 执行链路</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <MetricCard label="trace_id" value={trace?.trace_id || "未记录"} />
          <MetricCard label="问题类型" value={routeLabel(routeType)} />
          <MetricCard label="总阶段数" value={steps.length} />
          <MetricCard label="是否使用 LangGraph" value={usesLangGraph ? "是" : "否"} />
          <MetricCard label="回答生成" value={engineLabel(synthesizerStep?.engine)} />
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-950">执行阶段 Timeline</h2>
        <div className="mt-4 grid gap-3">
          {steps.length > 0 ? (
            steps.map((step, index) => (
              <TimelineStep key={`${step.stage}-${index}`} step={step} index={index} />
            ))
          ) : (
            <p className="rounded-md border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
              暂无 trace 阶段信息。
            </p>
          )}
        </div>
      </section>

      <ExecutorPanel step={executorStep} />
      <SynthesizerPanel step={synthesizerStep} />
      <EvaluationTracePanel step={evaluationStep} />
    </section>
  );
}
