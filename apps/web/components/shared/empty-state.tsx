type EmptyStateProps = {
  title?: string;
  description?: string;
  action?: { label: string; onClick: () => void };
};

export function EmptyState({
  title = "暂无数据",
  description = "当前没有可展示的内容。",
  action,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-12 text-center" style={{ borderColor: "var(--border)", color: "var(--text-tertiary)" }}>
      <div className="text-3xl mb-3">◌</div>
      <h3 className="text-sm font-semibold" style={{ color: "var(--text-secondary)" }}>{title}</h3>
      <p className="mt-1 text-xs max-w-md">{description}</p>
      {action && (
        <button onClick={action.onClick} className="mt-4 rounded-lg px-4 py-2 text-sm font-medium text-white" style={{ background: "var(--accent)" }}>
          {action.label}
        </button>
      )}
    </div>
  );
}
