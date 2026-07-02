"use client";

import { AppShell } from "@/components/layout/app-shell";
import { ProviderSelector } from "@/components/settings/provider-selector";
import { ModelSelector } from "@/components/settings/model-selector";
import { ThemeToggle } from "@/components/settings/theme-toggle";
import { EnvironmentPanel } from "@/components/settings/environment-panel";
import { SystemStatusPanel } from "@/components/settings/system-status-panel";
import { StatusBadge } from "@/components/shared/status-badge";
import { mockSettings } from "@/lib/mock/settings";

export default function SettingsPage() {
  return (
    <AppShell title="Settings">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>系统设置</h2>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            Provider 配置、模型选择、主题、运行环境和系统状态。
          </p>
        </div>
        <StatusBadge status="warning" label="Demo Mode — 仅 UI 展示" />
      </div>

      <div className="space-y-5">
        {/* Provider */}
        <ProviderSelector config={mockSettings.provider} />

        {/* Models */}
        <ModelSelector models={mockSettings.models} />

        {/* Theme + Env side by side */}
        <div className="grid gap-5 lg:grid-cols-2">
          <ThemeToggle current={mockSettings.theme} />
          <div className="card px-4 py-4">
            <p className="text-xs font-medium" style={{ color: "var(--text-tertiary)" }}>Config Source</p>
            <p className="mt-1 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{mockSettings.config_source}</p>
            <p className="mt-2 text-xs leading-5" style={{ color: "var(--text-tertiary)" }}>
              Settings saved locally for demo only. Backend configuration is still controlled by environment variables.
            </p>
          </div>
        </div>

        {/* Environment */}
        <EnvironmentPanel env={mockSettings.environment} />

        {/* System Status */}
        <SystemStatusPanel services={mockSettings.services} />
      </div>
    </AppShell>
  );
}
