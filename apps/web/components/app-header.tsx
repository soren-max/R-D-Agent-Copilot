export function AppHeader() {
  return (
    <header className="border-b border-slate-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-4 lg:px-8">
        <div className="flex flex-col">
          <h1 className="text-xl font-semibold tracking-tight text-slate-900">
            R&D Agent Copilot
          </h1>
          <p className="text-xs text-slate-500">AI 研发排障智能助手</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="badge-green">
            <span className="status-dot-success" />
            LangGraph
          </span>
          <span className="badge-slate">
            <span className="status-dot-success" />
            LocalAdapter
          </span>
          <span className="badge-blue">
            <span className="status-dot-pending" />
            DeepSeek Optional
          </span>
          <span className="badge-green">
            <span className="status-dot-success" />
            Trace
          </span>
        </div>
      </div>
    </header>
  );
}
