import type { PlanStep } from "@/lib/api";

type PlanViewerProps = {
  steps?: PlanStep[];
  routeType?: string;
};

function routeLabel(routeType: string | undefined) {
  if (routeType === "simple_qa") {
    return "简单问答";
  }
  if (routeType === "complex_troubleshooting") {
    return "复杂排障";
  }
  return routeType || "未知类型";
}

export function PlanViewer({ steps = [], routeType }: PlanViewerProps) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-950">路由与计划摘要</h2>
      <p className="mt-3 text-sm text-slate-700">问题类型：{routeLabel(routeType)}</p>
      <div className="mt-4 grid gap-3">
        {steps.length > 0 ? (
          steps.map((step) => (
            <article key={step.id} className="rounded-md border border-slate-200 bg-slate-50 p-4">
              <div className="flex flex-wrap gap-2 text-xs text-slate-600">
                <span>步骤 {step.id}</span>
                <span>动作：{step.action}</span>
                <span>工具：{step.tool}</span>
              </div>
              <p className="mt-2 text-sm text-slate-800">{step.description}</p>
            </article>
          ))
        ) : (
          <p className="rounded-md border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
            暂无任务规划信息。
          </p>
        )}
      </div>
    </section>
  );
}
