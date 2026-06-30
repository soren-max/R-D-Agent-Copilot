import type { LLMUsage } from "@/lib/api";

type LLMUsageCardProps = {
  usage?: LLMUsage | null;
  llmUsed?: boolean;
};

function formatNumber(value?: number) {
  if (typeof value !== "number" || Number.isNaN(value)) return "0";
  return value.toLocaleString("en-US");
}

function formatCost(value?: number, currency = "USD") {
  if (typeof value !== "number" || Number.isNaN(value)) return `${currency} 0.000000`;
  return `${currency} ${value.toFixed(6)}`;
}

function formatMs(value?: number) {
  if (typeof value !== "number" || Number.isNaN(value)) return "0ms";
  return `${Math.round(value)}ms`;
}

function sourceLabel(source?: string) {
  if (source === "api_usage") return "真实 API 返回";
  if (source === "estimated") return "估算";
  if (source === "llm_disabled") return "未启用";
  if (source === "fallback") return "Fallback";
  return source || "未知";
}

export function LLMUsageCard({ usage, llmUsed = false }: LLMUsageCardProps) {
  if (!usage) {
    return (
      <section className="card card-interactive">
        <div className="card-header">
          <h2 className="text-sm font-semibold text-slate-950">LLM Usage</h2>
        </div>
        <div className="card-body">
          <p className="text-sm text-slate-400">暂无 LLM 用量数据。</p>
        </div>
      </section>
    );
  }

  return (
    <section className="card card-interactive">
      <div className="card-header">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-sm font-semibold text-slate-950">LLM Usage</h2>
          <span className={llmUsed ? "badge-green" : "badge-slate"}>
            {llmUsed ? "Enabled" : "Disabled"}
          </span>
        </div>
      </div>
      <div className="card-body space-y-3">
        <UsageRow label="模型" value={usage.model || "deepseek-v4-flash"} />
        <UsageRow label="Provider" value={usage.provider || "deepseek"} />
        <UsageRow label="Prompt Tokens" value={formatNumber(usage.prompt_tokens)} mono />
        <UsageRow label="Completion Tokens" value={formatNumber(usage.completion_tokens)} mono />
        <UsageRow label="Total Tokens" value={formatNumber(usage.total_tokens)} mono />
        <UsageRow label="估算成本" value={formatCost(usage.estimated_cost, usage.currency || "USD")} mono />
        <UsageRow label="LLM 耗时" value={formatMs(usage.latency_ms)} mono />
        <UsageRow label="Source" value={sourceLabel(usage.source)} />
        <p className="pt-1 text-xs leading-5 text-slate-400">成本估算仅供本地演示参考，不作为真实计费依据。</p>
      </div>
    </section>
  );
}

function UsageRow({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-slate-100 pb-2.5 last:border-b-0 last:pb-0">
      <span className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</span>
      <span className={`max-w-[11rem] text-right text-xs font-semibold text-slate-800 ${mono ? "font-mono" : ""}`}>
        {value}
      </span>
    </div>
  );
}
