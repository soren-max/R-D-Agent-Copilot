import type { FinalReport } from "@/lib/api";

type Props = { report?: FinalReport | null };

export function FinalReportCard({ report }: Props) {
  if (!report) return null;
  return (
    <div className="card">
      <div className="card-header"><h3 className="text-sm font-semibold" style={{color:"var(--text-primary)"}}>Final Report</h3></div>
      <div className="card-body space-y-4">
        {report.summary && <Section label="Summary" value={report.summary} />}
        {report.root_cause && <Section label="Root Cause" value={report.root_cause} />}
        {report.evidence && report.evidence.length > 0 && (
          <div><p className="text-xs font-medium mb-1" style={{color:"var(--text-tertiary)"}}>Evidence</p><ul className="space-y-1">{report.evidence.map((e,i)=><li key={i} className="rounded-lg px-3 py-2 text-xs" style={{background:"var(--bg-subtle)",color:"var(--text-secondary)"}}>{e}</li>)}</ul></div>
        )}
        {report.fix_steps && report.fix_steps.length > 0 && (
          <div><p className="text-xs font-medium mb-1" style={{color:"var(--text-tertiary)"}}>Fix Steps</p><ul className="space-y-1">{report.fix_steps.map((s,i)=><li key={i} className="flex items-center gap-2 text-xs" style={{color:"var(--text-secondary)"}}><span className="dot-success" />{s}</li>)}</ul></div>
        )}
        <div className="flex flex-wrap gap-3 text-xs" style={{color:"var(--text-tertiary)"}}>
          <span>Confidence: <strong style={{color:"var(--text-primary)"}}>{report.confidence}</strong></span>
        </div>
        {report.risks && report.risks.length > 0 && (
          <div className="rounded-xl border px-4 py-3" style={{borderColor:"var(--warning-bg)",background:"var(--warning-bg)"}}>
            <p className="text-xs font-semibold mb-1" style={{color:"var(--warning)"}}>Risks</p>
            <ul className="space-y-1">{report.risks.map((r,i)=><li key={i} className="text-xs" style={{color:"var(--text-secondary)"}}>⚠ {r}</li>)}</ul>
          </div>
        )}
      </div>
    </div>
  );
}

function Section({label,value}:{label:string;value:string}){
  return <div><p className="text-xs font-medium mb-1" style={{color:"var(--text-tertiary)"}}>{label}</p><p className="text-sm leading-6" style={{color:"var(--text-primary)"}}>{value}</p></div>;
}
