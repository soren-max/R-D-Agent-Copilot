export function AppHeader() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-2 px-5 py-6 sm:px-8 lg:px-10">
        <p className="text-xs font-semibold text-emerald-700">执行链路查看器前端骨架</p>
        <h1 className="text-3xl font-semibold text-slate-950">R&D Agent Copilot</h1>
        <p className="text-base text-slate-600">AI 研发排障智能助手</p>
      </div>
    </header>
  );
}
