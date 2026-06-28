import type { PlanStep } from "@/lib/api";

type PlanViewerProps = {
  steps?: PlanStep[];
  routeType?: string;
};

function routeLabel(t: string | undefined) {
  if (t === "simple_qa") return { zh: "简单问答", en: "simple_qa", color: "badge-blue" };
  if (t === "complex_troubleshooting") return { zh: "复杂排障", en: "complex_troubleshooting", color: "badge-amber" };
  return { zh: t || "未知", en: t || "unknown", color: "badge-slate" };
}

export function PlanViewer({ steps = [], routeType }: PlanViewerProps) {
  const rt = routeLabel(routeType);

  return (
    <section className="card">
      <div className="card-header">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-slate-950">Route & Plan</h2>
            <p className="mt-1 text-xs text-slate-500">Router 分类结果与 Planner 生成的执行步骤。</p>
          </div>
          <span className={rt.color}>{rt.zh}</span>
        </div>
      </div>
      <div className="card-body">
        <div className="mb-4 grid gap-3 sm:grid-cols-2">
          <div className="rounded-2xl border border-slate-100 bg-slate-50/70 px-4 py-3">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">问题类型</p>
            <p className="mt-1 text-sm font-semibold text-slate-900">{rt.zh}</p>
          </div>
          <div className="rounded-2xl border border-slate-100 bg-slate-50/70 px-4 py-3">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Route Key</p>
            <p className="mt-1 font-mono text-sm font-semibold text-slate-900">{rt.en}</p>
          </div>
        </div>
        {steps.length > 0 ? (
          <div className="space-y-3">
            {steps.map((step, idx) => (
              <div key={step.id} className="relative flex items-start gap-3 rounded-2xl border border-slate-100 bg-white px-4 py-3 shadow-sm">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-950 font-mono text-xs font-semibold text-white">
                  {String(idx + 1).padStart(2, "0")}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-semibold text-slate-900">{step.action || "暂无数据"}</span>
                    <span className="rounded-full bg-slate-100 px-2 py-1 font-mono text-[11px] font-medium text-slate-600">
                      {step.tool || "暂无数据"}
                    </span>
                  </div>
                  <p className="mt-1 text-sm leading-6 text-slate-600">{step.description || "暂无数据"}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-400">暂无数据</p>
        )}
      </div>
    </section>
  );
}
