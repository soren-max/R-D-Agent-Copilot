const capabilities = [
  {
    title: "Agent 模式",
    desc: "Plan-Execute",
    icon: "01",
  },
  {
    title: "工具节点",
    desc: "Log / Config / Git / RAG",
    icon: "02",
  },
  {
    title: "执行引擎",
    desc: "LangGraph",
    icon: "03",
  },
  {
    title: "质量评估",
    desc: "Evaluation v1",
    icon: "04",
  },
];

export function HeroSection() {
  return (
    <section className="relative overflow-hidden rounded-2xl border border-slate-200/80 bg-white px-6 py-7 shadow-sm lg:px-8">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-emerald-400/70 to-transparent" />
      <div className="relative z-10">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
          <span className="dot-green" />
          Observable AI Agent Console
        </div>
        <h2 className="max-w-4xl text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
          执行链路可观测的研发排障 Agent
        </h2>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600 sm:text-[15px]">
          通过 Router、Planner、LangGraph Tool Nodes、RAG 和 Answer Synthesizer，
          将研发问题转化为可追踪、可评估的中文排障报告。
        </p>
        <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {capabilities.map((c) => (
            <div
              key={c.title}
              className="card-interactive rounded-2xl border border-slate-200 bg-slate-50/50 px-4 py-4"
            >
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm font-semibold text-slate-900">{c.title}</span>
                <span className="rounded-full bg-white px-2 py-1 font-mono text-[11px] font-semibold text-emerald-700 ring-1 ring-slate-200">
                  {c.icon}
                </span>
              </div>
              <p className="mt-2 text-xs font-medium text-slate-500">{c.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
