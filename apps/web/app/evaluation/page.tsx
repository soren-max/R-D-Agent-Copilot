"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { EvalMetricGrid } from "@/components/evaluation/eval-metric-grid";
import { RagEvalPanel } from "@/components/evaluation/rag-eval-panel";
import { PlanningEvalPanel } from "@/components/evaluation/planning-eval-panel";
import { BadCaseTable } from "@/components/evaluation/bad-case-table";
import { StatusBadge } from "@/components/shared/status-badge";
import { EmptyState } from "@/components/shared/empty-state";
import { mockEvalMetrics, mockRagEval, mockPlanningEval, mockBadCases } from "@/lib/mock/evaluation";

export default function EvaluationPage() {
  const [mode, setMode] = useState<"mock" | "live">("mock");
  const [hasLiveData] = useState(false);

  return (
    <AppShell title="Evaluation">
      {/* Header */}
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>质量评估仪表盘</h2>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            RAG Grounding、Planning 质量和安全指标的可量化评估体系。
          </p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={mode === "mock" ? "warning" : "success"} label={mode === "mock" ? "Mock Data" : "Live"} />
          {!hasLiveData && (
            <span className="rounded-md px-2.5 py-1 text-xs" style={{ background: "var(--bg-subtle)", color: "var(--text-tertiary)" }}>
              等待后端评估数据接入
            </span>
          )}
        </div>
      </div>

      {/* Top KPI cards */}
      <div className="mb-6">
        <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>核心指标</h3>
        <EvalMetricGrid
          routerAccuracy={mockEvalMetrics.routerAccuracy}
          toolsHitRate={mockEvalMetrics.toolsHitRate}
          planQuality={mockEvalMetrics.planQuality}
          groundingScore={mockEvalMetrics.groundingScore}
          unsupportedClaims={mockEvalMetrics.unsupportedClaims}
          noEvidenceRejection={mockEvalMetrics.noEvidenceRejection}
          safetyRecall={mockEvalMetrics.safetyRecall}
        />
      </div>

      {/* RAG + Planning panels */}
      <div className="mb-6 grid gap-5 lg:grid-cols-2">
        <RagEvalPanel
          recallAt5={mockRagEval.recallAt5}
          mrr={mockRagEval.mrr}
          groundingScore={mockRagEval.groundingScore}
          evidenceCoverage={mockRagEval.evidenceCoverage}
          unsupportedClaims={mockRagEval.unsupportedClaims}
          rejectionAccuracy={mockRagEval.rejectionAccuracy}
        />
        <PlanningEvalPanel
          intentScore={mockPlanningEval.intentScore}
          requiredToolsScore={mockPlanningEval.requiredToolsScore}
          stepOrderScore={mockPlanningEval.stepOrderScore}
          completenessScore={mockPlanningEval.completenessScore}
          safetyScore={mockPlanningEval.safetyScore}
          planQualityScore={mockPlanningEval.planQualityScore}
        />
      </div>

      {/* Bad Cases */}
      <BadCaseTable cases={mockBadCases} />

      {/* Benchmark summary */}
      <div className="card">
        <div className="card-header"><h3 className="text-sm font-semibold" style={{color:"var(--text-primary)"}}>Benchmark Summary</h3></div>
        <div className="card-body">
          <div className="rounded-xl border px-4 py-3" style={{borderColor:"var(--border)",background:"var(--bg-subtle)"}}>
            <p className="text-xs leading-5" style={{color:"var(--text-secondary)"}}>
              Benchmark 报告位于 <code className="font-mono" style={{color:"var(--accent)"}}>data/reports/benchmark_report.md</code>。
              包含 RAG Recall@K、MRR、Hit Rate、Router Accuracy、Tool Selection Accuracy 等指标。
              当前页面展示 Mock 评估面板作为 UI 参考，真实数据需通过后端 Evaluation API 或本地报告读取。
            </p>
          </div>
        </div>
      </div>

      {/* Footer: disclaimer */}
      <div className="mt-6 rounded-xl border px-4 py-3" style={{ borderColor: "var(--border)", background: "var(--bg-subtle)" }}>
        <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
          评估数据当前使用 Mock 数据展示。后端 Evaluation API 接入后会自动展示真实指标。
          Bad Cases 列表反映了 RAG 召回、Router 分类和 Safety Guard 的历史缺陷及修复进展。
        </p>
      </div>
    </AppShell>
  );
}
