"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { AppHeader } from "@/components/app-header";
import { AgentPipeline } from "@/components/agent-pipeline";
import { AnswerCard } from "@/components/answer-card";
import { ChatPanel } from "@/components/chat-panel";
import { PlanViewer } from "@/components/plan-viewer";
import { HeroSection } from "@/components/hero-section";
import { RunSummary } from "@/components/run-summary";
import { ToolEvidenceGrid } from "@/components/tool-evidence-grid";
import { TraceViewer } from "@/components/trace-viewer";
import { EvaluationPanel } from "@/components/evaluation-panel";
import { StreamingTimeline } from "@/components/streaming-timeline";
import { EvidencePanel } from "@/components/evidence-panel";
import { LLMUsageCard } from "@/components/llm-usage-card";
import { type AgentStreamEvent, type ChatResponse, chatStreamUrl, postChat } from "@/lib/api";

const examples = ["什么是配置中心？", "为什么订单接口报500？", "配置改了为什么不生效？"];

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
    if (!trimmed) {
      setNotice("请输入问题后再开始排查。");
      return;
    }
    setIsLoading(true);
    setIsStreaming(true);
    setError("");
    setNotice("");
    setResult(null);
    setStreamEvents([]);

    let completed = false;
    let fallbackStarted = false;
    const source = new EventSource(chatStreamUrl(trimmed));

    const appendEvent = (event: AgentStreamEvent) => {
      setStreamEvents((items) => [...items, event]);
    };

    const fallbackToChat = async () => {
      if (fallbackStarted || completed) return;
      fallbackStarted = true;
      source.close();
      setIsStreaming(false);
      setNotice("流式执行失败，已切换为普通请求。");
      try {
        const data = await postChat(trimmed);
        setResult(data);
      } catch {
        setError("请求失败，请确认后端服务是否已启动。");
      } finally {
        setIsLoading(false);
      }
    };

    const bind = (eventName: string) => {
      source.addEventListener(eventName, (message) => {
        const data = JSON.parse((message as MessageEvent).data) as AgentStreamEvent;
        appendEvent({ ...data, event: eventName });

        if (eventName === "completed") {
          completed = true;
          source.close();
          setIsStreaming(false);
          if (data.response) {
            setResult(data.response);
          }
          setIsLoading(false);
        }

        if (eventName === "error") {
          void fallbackToChat();
        }
      });
    };

    [
      "router_started",
      "router_completed",
      "planner_started",
      "planner_completed",
      "executor_started",
      "tool_started",
      "tool_completed",
      "synthesizer_started",
      "synthesizer_completed",
      "evaluation_started",
      "evaluation_completed",
      "completed",
      "error",
    ].forEach(bind);

    source.onerror = () => {
      void fallbackToChat();
    };
  }

  const routeType = result?.route?.type;

  return (
    <main className="min-h-screen">
      <AppHeader
        evaluation={result?.evaluation}
        trace={result?.trace}
        toolResults={result?.tool_results}
      />

      <div className="mx-auto max-w-[1440px] px-5 py-6 lg:px-8">
        <HeroSection />

        <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px] xl:grid-cols-[minmax(0,1fr)_400px]">
          <section className="min-w-0 space-y-5">
            <ChatPanel
              query={query}
              isLoading={isLoading}
              onQueryChange={(value) => {
                setQuery(value);
                setNotice("");
              }}
              onSubmit={handleSubmit}
              onExample={(value) => {
                setQuery(value);
                setNotice("");
              }}
            />

            {notice && (
              <div className="rounded-2xl border border-amber-200 bg-amber-50/70 px-4 py-3 text-sm font-medium text-amber-700">
                {notice}
              </div>
            )}

            {isLoading && !result && (
              <div className="card">
                <div className="card-body flex items-center gap-3 text-sm text-slate-500">
                  <svg className="h-4 w-4 animate-spin text-emerald-500" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Agent 正在分析中...
                </div>
              </div>
            )}

            <StreamingTimeline events={streamEvents} isStreaming={isStreaming} />

            {error && (
              <div className="rounded-2xl border border-red-200 bg-red-50/70 px-4 py-3 text-sm font-medium text-red-700">
                {error}
              </div>
            )}

            {result && (
              <>
                <AnswerCard
                  answer={result.answer}
                  answerSource={result.answer_source}
                  llmUsed={result.llm_used}
                  llmError={result.llm_error}
                />

                <PlanViewer steps={result.plan?.steps} routeType={routeType} />
                <ToolEvidenceGrid toolResults={result.tool_results} />
                <EvidencePanel evidenceChain={result.evidence_chain} />
                <TraceViewer trace={result.trace} routeType={routeType} />
                <EvaluationPanel evaluation={result.evaluation} />
              </>
            )}
          </section>

          <aside className="min-w-0">
            <div className="space-y-4 lg:sticky lg:top-[88px]">
              <AgentPipeline route={result?.route} trace={result?.trace} isLoading={isLoading} />
              <RunSummary result={result} isLoading={isLoading} />
              <LLMUsageCard usage={result?.llm_usage} llmUsed={result?.llm_used} />
            </div>
          </aside>
        </div>
      </div>
    </main>
  );
}
