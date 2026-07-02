import { StatusBadge } from "@/components/shared/status-badge";

type BadCase = {
  caseId: string;
  question: string;
  failureReason: string;
  status: "fixed" | "still_failed";
  expectedIntent: string;
  actualIntent: string;
  missingTools: string[];
};

type BadCaseTableProps = {
  cases?: BadCase[];
};

export function BadCaseTable({ cases }: BadCaseTableProps) {
  if (!cases || cases.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Bad Case Replay</h3>
        </div>
        <div className="card-body text-sm" style={{ color: "var(--text-tertiary)" }}>
          暂无 Bad Case 数据。
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Bad Case Replay</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-xs" style={{ borderColor: "var(--border-light)", color: "var(--text-tertiary)" }}>
              <th className="px-4 py-3 text-left font-medium">Case ID</th>
              <th className="px-4 py-3 text-left font-medium">Question</th>
              <th className="px-4 py-3 text-left font-medium">Failure Reason</th>
              <th className="px-4 py-3 text-left font-medium">Expected Intent</th>
              <th className="px-4 py-3 text-left font-medium">Actual Intent</th>
              <th className="px-4 py-3 text-left font-medium">Missing Tools</th>
              <th className="px-4 py-3 text-left font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {cases.map((bc) => (
              <tr key={bc.caseId} className="border-b" style={{ borderColor: "var(--border-light)" }}>
                <td className="px-4 py-3 font-mono text-xs" style={{ color: "var(--text-secondary)" }}>{bc.caseId}</td>
                <td className="max-w-xs truncate px-4 py-3" style={{ color: "var(--text-primary)" }}>{bc.question}</td>
                <td className="px-4 py-3" style={{ color: "var(--text-secondary)" }}>{bc.failureReason}</td>
                <td className="px-4 py-3 font-mono text-xs" style={{ color: "var(--text-secondary)" }}>{bc.expectedIntent}</td>
                <td className="px-4 py-3 font-mono text-xs" style={{ color: "var(--text-secondary)" }}>{bc.actualIntent}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {bc.missingTools.map((t) => (
                      <span key={t} className="rounded-md px-2 py-0.5 text-xs" style={{ background: "var(--warning-bg)", color: "var(--warning)" }}>{t}</span>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={bc.status === "fixed" ? "success" : "error"} label={bc.status === "fixed" ? "Fixed" : "Still Failed"} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
