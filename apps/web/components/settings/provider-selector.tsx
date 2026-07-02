import type { ProviderConfig } from "@/lib/mock/settings";

type Props = {
  config: ProviderConfig;
};

export function ProviderSelector({ config }: Props) {
  return (
    <div className="card">
      <div className="card-header"><h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>LLM Provider</h3></div>
      <div className="card-body space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          {["DeepSeek", "OpenAI-Compatible", "Mock"].map((p) => (
            <button
              key={p}
              className={`rounded-xl border-2 px-4 py-3.5 text-left transition-all ${
                config.provider === p ? "border-indigo-400 bg-indigo-50/50 dark:border-indigo-600 dark:bg-indigo-950/30" : "border-slate-200 hover:border-slate-300 dark:border-slate-700"
              }`}
            >
              <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{p}</p>
              <p className="mt-0.5 text-xs" style={{ color: "var(--text-tertiary)" }}>
                {p === "DeepSeek" ? "deepseek.com API" : p === "OpenAI-Compatible" ? "OpenAI API or proxy" : "Local deterministic responses"}
              </p>
            </button>
          ))}
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <p className="text-xs font-medium" style={{ color: "var(--text-tertiary)" }}>Current Model</p>
            <p className="mt-1 text-sm font-semibold font-mono" style={{ color: "var(--text-primary)" }}>{config.model}</p>
          </div>
          <div>
            <p className="text-xs font-medium" style={{ color: "var(--text-tertiary)" }}>API Base URL</p>
            <p className="mt-1 text-sm font-mono" style={{ color: "var(--text-primary)" }}>{config.api_base_url}</p>
          </div>
          <div>
            <p className="text-xs font-medium" style={{ color: "var(--text-tertiary)" }}>Timeout</p>
            <p className="mt-1 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{config.timeout}s</p>
          </div>
          <div>
            <p className="text-xs font-medium" style={{ color: "var(--text-tertiary)" }}>Streaming</p>
            <p className="mt-1 text-sm font-semibold" style={{ color: config.streaming_enabled ? "var(--success)" : "var(--text-tertiary)" }}>{config.streaming_enabled ? "Enabled" : "Disabled"}</p>
          </div>
        </div>

        <div className="rounded-xl border px-4 py-3" style={{ borderColor: "var(--border)", background: "var(--bg-subtle)" }}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium" style={{ color: "var(--text-tertiary)" }}>API Key</p>
              <p className="mt-1 font-mono text-sm" style={{ color: "var(--text-secondary)" }}>{config.api_key_masked}</p>
            </div>
            <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>Masked</span>
          </div>
          <p className="mt-2 text-xs" style={{ color: "var(--warning)" }}>敏感配置请通过后端 .env 设置，前端不保存真实 API Key。</p>
        </div>
      </div>
    </div>
  );
}
