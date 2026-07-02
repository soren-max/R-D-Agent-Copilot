"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { ChatPanel } from "@/components/chat-panel";
import { AnswerCard } from "@/components/answer-card";
import { PlanViewer } from "@/components/plan-viewer";
import { AgentPipeline } from "@/components/agent-pipeline";
import { RunSummary } from "@/components/run-summary";
import { ToolEvidenceGrid } from "@/components/tool-evidence-grid";
import { TraceViewer } from "@/components/trace-viewer";
import { EvaluationPanel } from "@/components/evaluation-panel";
import { StreamingTimeline } from "@/components/streaming-timeline";
import { EvidencePanel } from "@/components/evidence-panel";
import { RagPanel } from "@/components/rag-panel";
import { LLMUsageCard } from "@/components/llm-usage-card";
import { MetricCard } from "@/components/shared/metric-card";
import { type AgentStreamEvent, type ChatResponse, chatStreamUrl, postChat } from "@/lib/api";

export default function Home() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<ChatResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamEvents, setStreamEvents] = useState<AgentStreamEvent[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) { setNotice("请输入问题后再开始排查。"); return; }
    setIsLoading(true); setIsStreaming(true); setError(""); setNotice(""); setResult(null); setStreamEvents([]);

    let completed = false;
    let fallbackStarted = false;
    const source = new EventSource(chatStreamUrl(trimmed));

    const appendEvent = (evt: AgentStreamEvent) => setStreamEvents((items) => [...items, evt]);
    const fallbackToChat = async () => {
      if (fallbackStarted || completed) return;
      fallbackStarted = true; source.close(); setIsStreaming(false);
      setNotice("流式执行失败，已切换为普通请求。");
      try { const data = await postChat(trimmed); setResult(data); }
      catch { setError("请求失败，请确认后端服务是否已启动。"); }
      finally { setIsLoading(false); }
    };

    const bind = (eventName: string) => {
      source.addEventListener(eventName, (message) => {
        const data = JSON.parse((message as MessageEvent).data) as AgentStreamEvent;
        appendEvent({ ...data, event: eventName });
        if (eventName === "completed") { completed = true; source.close(); setIsStreaming(false); if (data.response) setResult(data.response); setIsLoading(false); }
        if (eventName === "error") { void fallbackToChat(); }
      });
    };

    ["router_started","router_completed","planner_started","planner_completed","executor_started","tool_started","tool_completed","synthesizer_started","synthesizer_completed","evaluation_started","evaluation_completed","completed","error"].forEach(bind);
    source.onerror = () => { void fallbackToChat(); };
  }

  const routeType = result?.route?.type;
  const toolResults = result?.tool_results;
  const evalScore = result?.evaluation?.overall_score;

  return (
    <AppShell title="Agent Console">
      {/* Quick metrics bar */}
      <div className="mb-5 grid gap-3 sm:grid-cols-4">
        <MetricCard label="意图识别" value={routeType === "complex_troubleshooting" ? "复杂排障" : routeType === "simple_qa" ? "简单问答" : ""} secondary={result?.route?.confidence ? `置信度 ${result.route.confidence}` : undefined} />
        <MetricCard label="工具调用" value={toolResults?.length ?? 0} secondary={toolResults?.filter(t => t.status === "success").length + " 成功"} />
        <MetricCard label="质量评分" value={evalScore != null ? `${Math.round(evalScore * 100)}%` : ""} />
        <MetricCard label="回答来源" value={result?.answer_source === "llm" ? "DeepSeek" : result?.answer_source ? "规则兜底" : ""} />
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <section className="min-w-0 space-y-5">
          <ChatPanel
            query={query}
            isLoading={isLoading}
            onQueryChange={(v) => { setQuery(v); setNotice(""); }}
            onSubmit={handleSubmit}
            onExample={(v) => { setQuery(v); setNotice(""); }}
          />

          {notice && <div className="card border-amber-200 bg-amber-50/70 px-4 py-3 text-sm font-medium" style={{color:"var(--warning)"}}>{notice}</div>}
          {isLoading && !result && !isStreaming && (
            <div className="card flex items-center gap-3 px-5 py-4 text-sm" style={{color:"var(--text-secondary)"}}>
              <svg className="h-4 w-4 animate-spin" style={{color:"var(--accent)"}} viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
              Agent 正在分析中...
            </div>
          )}

          <StreamingTimeline events={streamEvents} isStreaming={isStreaming} />
          {error && <div className="card border-red-200 bg-red-50/70 px-4 py-3 text-sm font-medium" style={{color:"var(--error)"}}>{error}</div>}

          {result && (
            <>
              <AnswerCard answer={result.answer} answerSource={result.answer_source} llmUsed={result.llm_used} llmError={result.llm_error} />
              <PlanViewer steps={result.plan?.steps} routeType={routeType} />
              <RagPanel result={result} />
              <ToolEvidenceGrid toolResults={result.tool_results} />
              <EvidencePanel evidenceChain={result.evidence_chain} />
              <TraceViewer trace={result.trace} routeType={routeType} />
              <EvaluationPanel evaluation={result.evaluation} />
            </>
          )}
        </section>

        <aside className="min-w-0">
          <div className="space-y-4 lg:sticky lg:top-20">
            {!result && !isLoading && (
              <div className="card px-5 py-6 text-center">
                <div className="text-2xl mb-3" style={{ color: "var(--text-muted)" }}>◌</div>
                <p className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>等待执行</p>
                <p className="mt-1 text-xs leading-5" style={{ color: "var(--text-tertiary)" }}>
                  输入研发故障问题，点击开始排障<br />即可查看完整 Agent 执行链路
                </p>
              </div>
            )}
            <AgentPipeline route={result?.route} trace={result?.trace} isLoading={isLoading} />
            <RunSummary result={result} isLoading={isLoading} />
            <LLMUsageCard usage={result?.llm_usage} llmUsed={result?.llm_used} />
          </div>
        </aside>
      </div>
    </AppShell>
  );
}
