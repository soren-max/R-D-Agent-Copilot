import { ScoreBar } from "@/components/shared/score-bar";

type PlanningEvalPanelProps = {
  intentScore?: number;
  requiredToolsScore?: number;
  stepOrderScore?: number;
  completenessScore?: number;
  safetyScore?: number;
  planQualityScore?: number;
};

const items: Array<{ key: keyof PlanningEvalPanelProps; label: string }> = [
  { key: "intentScore", label: "Intent Score" },
  { key: "requiredToolsScore", label: "Required Tools" },
  { key: "stepOrderScore", label: "Step Order" },
  { key: "completenessScore", label: "Completeness" },
  { key: "safetyScore", label: "Safety" },
  { key: "planQualityScore", label: "Plan Quality" },
];

export function PlanningEvalPanel(props: PlanningEvalPanelProps) {
  const hasData = Object.values(props).some((v) => v != null);

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Planning Evaluation</h3>
      </div>
      <div className="card-body grid gap-4 sm:grid-cols-2">
        {items.map(({ key, label }) => (
          <div key={key}>
            {props[key] != null ? (
              <ScoreBar label={label} value={Math.round(props[key]! * 100)} size="md" />
            ) : (
              <div className="text-sm" style={{ color: "var(--text-tertiary)" }}>
                <p>{label}</p>
                <p className="mt-1">—</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
