type ScoreBarProps = {
  value: number;
  max?: number;
  label?: string;
  showValue?: boolean;
  size?: "sm" | "md";
};

const sizeMap = {
  sm: { bar: "h-1.5", text: "text-xs" },
  md: { bar: "h-2", text: "text-sm" },
};

function scoreColor(value: number): string {
  if (value >= 85) return "var(--success)";
  if (value >= 70) return "var(--accent)";
  if (value >= 50) return "var(--warning)";
  return "var(--error)";
}

export function ScoreBar({ value, max = 100, label, showValue = true, size = "sm" }: ScoreBarProps) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  const s = sizeMap[size];

  return (
    <div>
      {(label || showValue) && (
        <div className="mb-1 flex items-center justify-between">
          {label && <span className={s.text} style={{ color: "var(--text-tertiary)" }}>{label}</span>}
          {showValue && (
            <span className={`font-semibold ${s.text}`} style={{ color: scoreColor(pct) }}>
              {Math.round(pct)}%
            </span>
          )}
        </div>
      )}
      <div className="w-full rounded-full" style={{ background: "var(--bg-subtle)", height: s.bar }}>
        <div
          className="rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, background: scoreColor(pct), height: s.bar }}
        />
      </div>
    </div>
  );
}
