const capabilities = [
  {
    title: "智能分流",
    desc: "Simple QA / Complex Troubleshooting",
    icon: "▶",
  },
  {
    title: "工具编排",
    desc: "Log / Config / Git / RAG",
    icon: "⚙",
  },
  {
    title: "Trace 可观测",
    desc: "Node / Tool Call / Retry / Fallback",
    icon: "◉",
  },
  {
    title: "质量评估",
    desc: "Evaluation Score / Evidence Grounding",
    icon: "◎",
  },
];

export function HeroSection() {
  return (
    <section className="relative overflow-hidden rounded-2xl border border-slate-200 bg-gradient-to-br from-white to-emerald-50/40 px-8 py-10">
      <div className="relative z-10">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
          执行链路可观测的研发排障 Agent
        </h2>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
          输入研发问题后，系统会经过 Router、Planner、LangGraph Tool Nodes、RAG 和 Answer
          Synthesizer，生成可追踪、可评估的中文排障报告。
        </p>
        <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {capabilities.map((c) => (
            <div
              key={c.title}
              className="rounded-xl border border-slate-200/70 bg-white/70 px-4 py-3.5 backdrop-blur-sm transition-colors hover:border-emerald-200/60"
            >
              <div className="flex items-center gap-2">
                <span className="text-sm text-emerald-600">{c.icon}</span>
                <span className="text-sm font-semibold text-slate-800">{c.title}</span>
              </div>
              <p className="mt-1 text-xs text-slate-500">{c.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
