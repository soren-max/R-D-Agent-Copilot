type LoadingStateProps = {
  message?: string;
};

export function LoadingState({ message = "正在加载..." }: LoadingStateProps) {
  return (
    <div className="flex items-center justify-center gap-3 rounded-2xl border px-6 py-12" style={{ borderColor: "var(--border)" }}>
      <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none" style={{ color: "var(--accent)" }}>
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      <span className="text-sm" style={{ color: "var(--text-secondary)" }}>{message}</span>
    </div>
  );
}
