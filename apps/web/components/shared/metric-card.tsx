type MetricCardProps = {
  label: string;
  value: string | number;
  trend?: "up" | "down" | "neutral";
  secondary?: string;
};

export function MetricCard({ label, value, trend, secondary }: MetricCardProps) {
  const trendColors = {
    up: "text-emerald-600",
    down: "text-red-600",
    neutral: "text-slate-500",
  };
  const trendArrows = {
    up: "↑",
    down: "↓",
    neutral: "→",
  };

  const isEmpty = value === "—" || value === "" || value === undefined || value === null;

  return (
    <div className={`card px-4 py-3.5 transition-all ${isEmpty ? "opacity-50" : ""}`}>
      <p className="text-xs font-medium" style={{ color: "var(--text-tertiary)" }}>
        {label}
      </p>
      <div className="mt-1 flex items-baseline gap-2">
        <span className={`metric-value ${isEmpty ? "font-normal" : ""}`} style={{ color: isEmpty ? "var(--text-muted)" : "var(--text-primary)" }}>
          {isEmpty ? "暂无数据" : value}
        </span>
        {trend && (
          <span className={`text-sm font-semibold ${trendColors[trend]}`}>
            {trendArrows[trend]}
          </span>
        )}
      </div>
      {secondary && (
        <p className="mt-0.5 text-xs" style={{ color: "var(--text-tertiary)" }}>
          {secondary}
        </p>
      )}
    </div>
  );
}
