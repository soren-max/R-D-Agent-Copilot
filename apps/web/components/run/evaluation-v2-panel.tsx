import type { EvaluationV2Metrics } from "@/lib/api";

type Props = { evaluationV2?: EvaluationV2Metrics | null };
const groups: Array<{key:keyof EvaluationV2Metrics;label:string}> = [
  {key:"context",label:"Context"},{key:"tool",label:"Tool"},{key:"rag",label:"RAG"},
  {key:"memory",label:"Memory"},{key:"resume",label:"Resume"},{key:"evidence",label:"Evidence"},{key:"provider",label:"Provider"},
];

export function EvaluationV2Panel({ evaluationV2 }: Props) {
  if (!evaluationV2) return null;
  return (
    <div className="card">
      <div className="card-header"><h3 className="text-sm font-semibold" style={{color:"var(--text-primary)"}}>Evaluation v2</h3></div>
      <div className="card-body grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {groups.map(({key,label})=>{
          const metrics = evaluationV2[key];
          if(!metrics || Object.keys(metrics).length===0) return null;
          return (
            <div key={key} className="rounded-xl border px-4 py-3" style={{borderColor:"var(--border)"}}>
              <p className="text-xs font-semibold mb-2" style={{color:"var(--text-tertiary)"}}>{label}</p>
              <div className="space-y-1.5">
                {Object.entries(metrics).map(([k,v])=>(
                  <div key={k} className="flex items-center justify-between text-xs">
                    <span style={{color:"var(--text-secondary)"}}>{k}</span>
                    <span className="font-semibold" style={{color:"var(--text-primary)"}}>{typeof v === "number" ? v.toFixed(2) : v}</span>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
