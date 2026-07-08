const steps = [
  { id: "router", label: "Router", desc: "意图分类", color: "#6366f1" },
  { id: "planner", label: "Planner", desc: "任务拆解", color: "#0284c7" },
  { id: "executor", label: "LangGraph", desc: "工具编排", color: "#d97706" },
  { id: "tools", label: "Tools/RAG", desc: "证据检索", color: "#059669" },
  { id: "synthesizer", label: "Synthesizer", desc: "回答生成", color: "#8b5cf6" },
  { id: "evaluation", label: "Eval", desc: "质量评估", color: "#0f172a" },
];

export function AgentPipelineStepper() {
  return (
    <div className="flex items-center gap-0">
      {steps.map((s, i) => (
        <div key={s.id} className="flex items-center gap-0 flex-1">
          <div className="flex flex-col items-center min-w-0">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-white" style={{ background: s.color }}>{i + 1}</div>
            <span className="mt-1 text-[10px] font-semibold leading-tight text-center" style={{ color: "var(--text-secondary)" }}>{s.label}</span>
            <span className="text-[9px]" style={{ color: "var(--text-tertiary)" }}>{s.desc}</span>
          </div>
          {i < steps.length - 1 && <div className="flex-1 h-px mx-1 mb-5" style={{ background: "var(--border)" }} />}
        </div>
      ))}
    </div>
  );
}
