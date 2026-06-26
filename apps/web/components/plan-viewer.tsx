import type { PlanStep } from "@/lib/api";

type PlanViewerProps = {
  steps?: PlanStep[];
  routeType?: string;
};

function routeLabel(t: string | undefined) {
  if (t === "simple_qa") return { zh: "简单问答", en: "simple_qa", color: "text-blue-600 bg-blue-50" };
  if (t === "complex_troubleshooting") return { zh: "复杂排障", en: "complex_troubleshooting", color: "text-amber-600 bg-amber-50" };
  return { zh: t || "未知", en: t || "unknown", color: "text-slate-600 bg-slate-100" };
}

export function PlanViewer({ steps = [], routeType }: PlanViewerProps) {
  const rt = routeLabel(routeType);

  return (
    <div className="card p-5">
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="text-sm font-semibold text-slate-900">路由与计划</h2>
        <span className={`badge ${rt.color}`}>{rt.zh}</span>
      </div>
      {steps.length > 0 ? (
        <div className="mt-4 space-y-2">
          {steps.map((step, idx) => (
            <div
              key={step.id}
              className="flex items-start gap-3 rounded-xl border border-slate-100 bg-slate-50/50 px-4 py-3"
            >
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-xs font-semibold text-emerald-700">
                {idx + 1}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
                  <span className="font-medium text-slate-700">{step.action}</span>
                  <span className="rounded bg-slate-200/60 px-1.5 py-0.5 text-slate-600">
                    {step.tool}
                  </span>
                </div>
                <p className="mt-1 text-sm text-slate-700">{step.description}</p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-4 text-sm text-slate-400">暂无计划信息。</p>
      )}
    </div>
  );
}
