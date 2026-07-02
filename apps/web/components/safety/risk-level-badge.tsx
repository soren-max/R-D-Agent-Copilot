import type { RiskLevel } from "@/lib/mock/safety";

type Props = { level: RiskLevel };

const config: Record<RiskLevel, { label: string; dot: string; bg: string; text: string }> = {
  low:      { label: "Low",      dot: "var(--text-muted)", bg: "var(--bg-subtle)", text: "var(--text-tertiary)" },
  medium:   { label: "Medium",   dot: "var(--warning)",    bg: "var(--warning-bg)", text: "var(--warning)" },
  high:     { label: "High",     dot: "var(--error)",      bg: "var(--error-bg)", text: "var(--error)" },
  critical: { label: "Critical", dot: "#dc2626",  bg: "#fef2f2",   text: "#dc2626" },
};

export function RiskLevelBadge({ level }: Props) {
  const c = config[level];
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium" style={{ background: c.bg, color: c.text }}>
      <span className="inline-block h-1.5 w-1.5 rounded-full" style={{ background: c.dot }} />
      {c.label}
    </span>
  );
}
