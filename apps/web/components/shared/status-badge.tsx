type StatusBadgeProps = {
  status: string;
  label?: string;
};

const config: Record<string, { dot: string; bg: string }> = {
  success:  { dot: "var(--success)", bg: "var(--success-bg)" },
  failed:   { dot: "var(--error)", bg: "var(--error-bg)" },
  error:    { dot: "var(--error)", bg: "var(--error-bg)" },
  warning:  { dot: "var(--warning)", bg: "var(--warning-bg)" },
  skipped:  { dot: "var(--text-muted)", bg: "var(--bg-subtle)" },
  pending:  { dot: "var(--text-muted)", bg: "var(--bg-subtle)" },
};

const labels: Record<string, string> = {
  success: "成功", failed: "失败", error: "错误",
  warning: "警告", skipped: "已跳过", pending: "等待中",
};

export function StatusBadge({ status, label }: StatusBadgeProps) {
  const cfg = config[status] || { dot: "var(--text-muted)", bg: "var(--bg-subtle)" };
  const text = label || labels[status] || status;
  const textColor = status === "success" ? "var(--success)" :
    status === "failed" || status === "error" ? "var(--error)" :
    status === "warning" ? "var(--warning)" : "var(--text-secondary)";

  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium"
      style={{ background: cfg.bg, color: textColor }}
    >
      <span className="inline-block h-1.5 w-1.5 rounded-full" style={{ background: cfg.dot }} />
      {text}
    </span>
  );
}
