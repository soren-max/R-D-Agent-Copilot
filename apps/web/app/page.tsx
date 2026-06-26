"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { AppHeader } from "@/components/app-header";
import { HeroSection } from "@/components/hero-section";
import { ChatPanel } from "@/components/chat-panel";
import { AgentPipeline } from "@/components/agent-pipeline";
import { AnswerCard } from "@/components/answer-card";
import { PlanViewer } from "@/components/plan-viewer";
import { ToolResultCard } from "@/components/tool-result-card";
import { TraceViewer } from "@/components/trace-viewer";
import { EvaluationPanel } from "@/components/evaluation-panel";
import { type ChatResponse, postChat } from "@/lib/api";

export default function Home() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<ChatResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
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
    setError("");
    setNotice("");
    try {
      const data = await postChat(trimmed);
      setResult(data);
    } catch {
      setError("请求失败，请确认后端服务是否已启动。");
    } finally {
      setIsLoading(false);
    }
  }

  function handleExample(v: string) {
    setQuery(v);
    setNotice("");
  }

  const routeType = result?.route?.type;

  return (
    <main className="min-h-screen bg-slate-50">
      <AppHeader />

      <div className="mx-auto max-w-7xl px-6 py-8 lg:px-8">
        {/* Hero */}
        <HeroSection />

        {/* Main area: Chat + Pipeline side by side */}
        <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_320px]">
          {/* Left: Chat + Results */}
          <div className="min-w-0 space-y-5">
            {/* Input */}
            <ChatPanel
              query={query}
              isLoading={isLoading}
              onQueryChange={setQuery}
              onSubmit={handleSubmit}
              onExample={handleExample}
            />

            {/* Notice */}
            {notice && (
              <div className="rounded-xl border border-amber-200 bg-amber-50/50 px-4 py-3 text-sm text-amber-700">
                {notice}
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="rounded-xl border border-red-200 bg-red-50/50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            {/* Loading indicator */}
            {isLoading && !result && (
              <div className="card flex items-center gap-3 px-5 py-4 text-sm text-slate-500">
                <svg className="h-4 w-4 animate-spin text-emerald-500" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Agent 正在分析中...
              </div>
            )}

            {/* Results */}
            {result && (
              <>
                {/* Answer */}
                <AnswerCard
                  answer={result.answer}
                  answerSource={result.answer_source}
                  llmUsed={result.llm_used}
                  llmError={result.llm_error}
                />

                {/* Route & Plan */}
                <PlanViewer steps={result.plan?.steps} routeType={routeType} />

                {/* Tool Results */}
                {result.tool_results && result.tool_results.length > 0 && (
                  <div className="card p-5">
                    <h2 className="text-sm font-semibold text-slate-900">工具结果摘要</h2>
                    <div className="mt-4 grid gap-3 sm:grid-cols-2">
                      {result.tool_results.map((tr, i) => (
                        <ToolResultCard key={`${tr.tool_name || tr.tool}-${i}`} toolResult={tr} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Trace */}
                <TraceViewer trace={result.trace} routeType={routeType} />

                {/* Evaluation */}
                <EvaluationPanel evaluation={(result as any).evaluation} />
              </>
            )}
          </div>

          {/* Right: Agent Pipeline Status (sticky) */}
          <div className="lg:sticky lg:top-24 lg:self-start">
            <AgentPipeline route={result?.route} trace={result?.trace} isLoading={isLoading} />
          </div>
        </div>
      </div>
    </main>
  );
}
