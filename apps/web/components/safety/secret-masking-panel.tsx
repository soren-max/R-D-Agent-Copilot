import type { SecretExample } from "@/lib/mock/safety";

type Props = { secrets: SecretExample[] };

export function SecretMaskingPanel({ secrets }: Props) {
  return (
    <div className="card">
      <div className="card-header"><h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Secret Masking</h3></div>
      <div className="divide-y" style={{ borderColor: "var(--border-light)" }}>
        {secrets.map((sec, i) => (
          <div key={i} className="px-4 py-3.5">
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{sec.secret_type}</p>
                <div className="mt-2 grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-[10px] font-medium uppercase tracking-wider" style={{ color: "var(--text-tertiary)" }}>Original</p>
                    <pre className="mt-1 truncate rounded-lg px-3 py-2 text-xs font-mono" style={{ background: "var(--bg-subtle)", color: "var(--error)" }}>{sec.original_example}</pre>
                  </div>
                  <div>
                    <p className="text-[10px] font-medium uppercase tracking-wider" style={{ color: "var(--text-tertiary)" }}>Masked</p>
                    <pre className="mt-1 truncate rounded-lg px-3 py-2 text-xs font-mono" style={{ background: "var(--success-bg)", color: "var(--success)" }}>{sec.masked_example}</pre>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
