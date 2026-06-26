"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { AppHeader } from "@/components/app-header";
import { AgentPipeline } from "@/components/agent-pipeline";
import { PlanViewer } from "@/components/plan-viewer";
import { ToolResultCard } from "@/components/tool-result-card";
import { TraceViewer } from "@/components/trace-viewer";
import { EvaluationPanel } from "@/components/evaluation-panel";
import { type ChatResponse, postChat } from "@/lib/api";

const examples = ["什么是配置中心？", "为什么订单接口报500？", "配置改了为什么不生效？"];

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

  const routeType = result?.route?.type;

  return (
    <main className="min-h-screen bg-slate-50">
      <AppHeader
        evaluation={result?.evaluation}
        trace={result?.trace}
        toolResults={result?.tool_results}
      />

      <div className="mx-auto max-w-7xl px-6 py-6 lg:px-8">
        <div className="card mb-6">
          <div className="card-body">
            <p className="text-sm leading-6 text-slate-600">
              输入研发问题后，系统会经过 Router、Planner、LangGraph Tool Nodes、RAG 和 Answer Synthesizer，
              生成可追踪、可评估的中文排障报告。
            </p>
          </div>
        </div>

        <div className="flex gap-6 lg:flex-row flex-col">
          <div className="flex-1 min-w-0 space-y-4">
            <form onSubmit={handleSubmit} className="card">
              <div className="card-header">
                <label htmlFor="query" className="text-sm font-semibold text-slate-900">
                  研发问题输入
                </label>
              </div>
              <div className="card-body space-y-4">
                <textarea
                  id="query"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="例如：为什么订单接口报500？配置改了但没有生效，应该怎么排查？"
                  rows={4}
                  className="w-full resize-y rounded-xl border border-slate-200 bg-slate-50/50 px-4 py-3 text-sm leading-6 text-slate-900 placeholder:text-slate-400 transition-colors focus:bg-white focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400"
                />
                <div className="flex flex-wrap items-center gap-2.5">
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-emerald-700 active:scale-[0.98] disabled:cursor-not-allowed disabled:bg-slate-300"
                  >
                    {isLoading ? (
                      <>
                        <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        Agent 分析中...
                      </>
                    ) : "开始排查"}
                  </button>
                  {examples.map((ex) => (
                    <button
                      key={ex}
                      type="button"
                      disabled={isLoading}
                      onClick={() => { setQuery(ex); setNotice(""); }}
                      className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-600 transition-colors hover:border-emerald-300 hover:text-emerald-700 disabled:opacity-50"
                    >
                      {ex}
                    </button>
                  ))}
                </div>
                {notice && <p className="text-sm text-amber-700">{notice}</p>}
                {isLoading && (
                  <p className="text-xs text-slate-400">
                    正在执行 Router → Planner → LangGraph Tools → Synthesizer
                  </p>
                )}
              </div>
            </form>

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

            {error && (
              <div className="rounded-xl border border-red-200 bg-red-50/50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            {result && (
              <>
                <div className="card">
                  <div className="card-header flex flex-wrap items-center gap-2">
                    <h2 className="text-sm font-semibold text-slate-900">Agent 排障报告</h2>
                    <span className={`badge ${result.answer_source === "llm" ? "badge-blue" : "badge-slate"}`}>
                      {result.answer_source === "llm" ? "DeepSeek 生成" : "规则兜底"}
                    </span>
                    <span className={`badge ${result.llm_used ? "badge-green" : "badge-slate"}`}>
                      {result.llm_used ? "LLM 已启用" : "LLM 未启用"}
                    </span>
                  </div>
                  <div className="card-body">
                    <p className="whitespace-pre-wrap text-sm leading-7 text-slate-800">{result.answer}</p>
                    {result.llm_error && (
                      <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">
                        LLM 状态：{result.llm_error}
                      </p>
                    )}
                  </div>
                </div>

                <PlanViewer steps={result.plan?.steps} routeType={routeType} />

                {result.tool_results && result.tool_results.length > 0 && (
                  <div className="card">
                    <div className="card-header">
                      <h2 className="text-sm font-semibold text-slate-900">工具结果摘要</h2>
                    </div>
                    <div className="card-body grid gap-3 sm:grid-cols-2">
                      {result.tool_results.map((tr, i) => (
                        <ToolResultCard key={`${tr.tool_name || tr.tool}-${i}`} toolResult={tr} />
                      ))}
                    </div>
                  </div>
                )}

                <TraceViewer trace={result.trace} routeType={routeType} />
                <EvaluationPanel evaluation={result.evaluation} />
              </>
            )}
          </div>

          <div className="lg:w-72 lg:shrink-0">
            <div className="lg:sticky lg:top-20">
              <AgentPipeline route={result?.route} trace={result?.trace} isLoading={isLoading} />
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
