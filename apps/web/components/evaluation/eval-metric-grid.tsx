import { MetricCard } from "@/components/shared/metric-card";

type EvalMetricGridProps = {
  routerAccuracy?: number;
  toolsHitRate?: number;
  planQuality?: number;
  groundingScore?: number;
  unsupportedClaims?: number;
  noEvidenceRejection?: number;
  safetyRecall?: number;
};

export function EvalMetricGrid(props: EvalMetricGridProps) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <MetricCard label="Router Accuracy" value={props.routerAccuracy != null ? `${Math.round(props.routerAccuracy * 100)}%` : "—"} />
      <MetricCard label="Tools Hit Rate" value={props.toolsHitRate != null ? `${Math.round(props.toolsHitRate * 100)}%` : "—"} />
      <MetricCard label="Plan Quality" value={props.planQuality != null ? `${Math.round(props.planQuality * 100)}%` : "—"} />
      <MetricCard label="Grounding Score" value={props.groundingScore != null ? `${Math.round(props.groundingScore * 100)}%` : "—"} />
      <MetricCard label="Unsupported Claims" value={props.unsupportedClaims ?? "—"} />
      <MetricCard label="No Evidence Rejection" value={props.noEvidenceRejection != null ? `${Math.round(props.noEvidenceRejection * 100)}%` : "—"} />
      <MetricCard label="Safety Recall" value={props.safetyRecall != null ? `${Math.round(props.safetyRecall * 100)}%` : "—"} />
    </div>
  );
}
