"use client";

import { AppShell } from "@/components/layout/app-shell";
import { SafetySummaryCards } from "@/components/safety/safety-summary-cards";
import { SafetyPolicyCard } from "@/components/safety/safety-policy-card";
import { RiskEventTable } from "@/components/safety/risk-event-table";
import { UnsafeCommandPanel } from "@/components/safety/unsafe-command-panel";
import { PromptInjectionPanel } from "@/components/safety/prompt-injection-panel";
import { SecretMaskingPanel } from "@/components/safety/secret-masking-panel";
import { StatusBadge } from "@/components/shared/status-badge";
import {
  mockSafetyStats,
  mockPolicies,
  mockRiskEvents,
  mockUnsafeCommands,
  mockInjections,
  mockSecrets,
} from "@/lib/mock/safety";

export default function SafetyPage() {
  return (
    <AppShell title="Safety Guard">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>安全防护控制台</h2>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            Agent 安全策略、风险事件、高危命令检测和敏感信息脱敏监控。
          </p>
        </div>
        <StatusBadge status="success" label="Mock Data" />
      </div>

      {/* Summary Cards */}
      <div className="mb-5">
        <SafetySummaryCards stats={mockSafetyStats} />
      </div>

      {/* Policies */}
      <div className="mb-5">
        <div className="card-header mb-0 rounded-t-xl border" style={{ borderColor: "var(--border)", background: "var(--bg-card)", borderBottom: "none" }}>
          <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Safety Policies</h3>
        </div>
        <div className="grid gap-3 border border-t-0 rounded-b-xl p-3" style={{ borderColor: "var(--border)", background: "var(--bg-card)" }}>
          {mockPolicies.map((p) => (
            <SafetyPolicyCard key={p.policy_name} policy={p} />
          ))}
        </div>
      </div>

      {/* Risk Events */}
      <div className="mb-5">
        <RiskEventTable events={mockRiskEvents} />
      </div>

      {/* Two-column: Unsafe Commands + Prompt Injection */}
      <div className="mb-5 grid gap-5 lg:grid-cols-2">
        <UnsafeCommandPanel commands={mockUnsafeCommands} />
        <PromptInjectionPanel injections={mockInjections} />
      </div>

      {/* Secret Masking */}
      <div className="mb-5">
        <SecretMaskingPanel secrets={mockSecrets} />
      </div>

      {/* Impact notice */}
      <div className="rounded-xl border px-4 py-3" style={{ borderColor: "var(--border)", background: "var(--bg-subtle)" }}>
        <p className="text-xs leading-5" style={{ color: "var(--text-tertiary)" }}>
          安全数据当前使用 Mock 数据展示。已拦截 {mockSafetyStats.blocked_actions} 次风险操作，检测到 {mockSafetyStats.injection_attempts} 次 Prompt Injection 尝试，脱敏 {mockSafetyStats.secret_masked_count} 条敏感信息。所有示例中的密钥、Token 和密码均为伪造，不涉及真实凭据。
        </p>
      </div>
    </AppShell>
  );
}
