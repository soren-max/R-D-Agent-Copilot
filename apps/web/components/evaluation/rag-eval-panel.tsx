import { ScoreBar } from "@/components/shared/score-bar";
import { MetricCard } from "@/components/shared/metric-card";

type RagEvalPanelProps = {
  recallAt5?: number;
  mrr?: number;
  groundingScore?: number;
  evidenceCoverage?: number;
  unsupportedClaims?: number;
  rejectionAccuracy?: number;
};

export function RagEvalPanel(props: RagEvalPanelProps) {
  const items = [
    { label: "Recall@5", value: props.recallAt5 },
    { label: "MRR", value: props.mrr },
    { label: "Grounding Score", value: props.groundingScore },
    { label: "Evidence Coverage", value: props.evidenceCoverage },
    { label: "Unsupported Claims", value: props.unsupportedClaims },
    { label: "Rejection Accuracy", value: props.rejectionAccuracy },
  ];

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>RAG Evaluation</h3>
      </div>
      <div className="card-body grid gap-4 sm:grid-cols-2">
        {items.map((item) => (
          <div key={item.label}>
            {item.value != null ? (
              <ScoreBar label={item.label} value={Math.round(item.value * 100)} size="md" />
            ) : (
              <div className="text-sm" style={{ color: "var(--text-tertiary)" }}>
                <p>{item.label}</p>
                <p className="mt-1">—</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
