"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { AppHeader } from "@/components/app-header";
import { EvaluationPanel } from "@/components/evaluation-panel";
import { PlanViewer } from "@/components/plan-viewer";
import { ToolResultCard } from "@/components/tool-result-card";
import { TraceViewer } from "@/components/trace-viewer";
import { type ChatResponse, postChat } from "@/lib/api";

const examples = ["什么是配置中心？", "为什么订单接口报500？"];

function answerSourceLabel(source: string | undefined) {
  if (source === "llm") {
    return "DeepSeek 生成回答";
  }
  return "规则兜底回答";
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<ChatResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedQuery = query.trim();

    if (!trimmedQuery) {
      setNotice("请输入问题后再开始排查。");
      setError("");
      return;
    }

    setIsLoading(true);
    setError("");
    setNotice("");

    try {
      const data = await postChat(trimmedQuery);
      setResult(data);
    } catch {
      setError("请求失败，请确认后端服务是否已启动。");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50">
      <AppHeader />
      <section className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-5 py-8 sm:px-8 lg:px-10">
        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <p className="max-w-3xl text-sm leading-6 text-slate-700">
            输入研发问题后，系统会经过 Router、Planner、LangGraph Tool Nodes 和 Answer Synthesizer
            生成可追踪回答。
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
        >
          <label htmlFor="query" className="text-base font-semibold text-slate-950">
            对话输入区
          </label>
          <textarea
            id="query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="请输入研发问题，例如：为什么订单接口报500？"
            className="mt-3 min-h-32 w-full resize-y rounded-md border border-slate-300 px-3 py-3 text-sm leading-6 text-slate-900 outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100"
          />
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={isLoading}
              className="rounded-md bg-emerald-700 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
            >
              开始排查
            </button>
            {examples.map((example) => (
              <button
                key={example}
                type="button"
                onClick={() => {
                  setQuery(example);
                  setNotice("");
                }}
                className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:border-emerald-600 hover:text-emerald-700"
              >
                {example}
              </button>
            ))}
          </div>
          {notice ? <p className="mt-3 text-sm text-amber-700">{notice}</p> : null}
        </form>

        {isLoading ? (
          <section className="rounded-lg border border-slate-200 bg-white p-5 text-sm text-slate-700 shadow-sm">
            Agent 正在分析中...
          </section>
        ) : null}

        {error ? (
          <section className="rounded-lg border border-red-200 bg-red-50 p-5 text-sm text-red-700">
            {error}
          </section>
        ) : null}

        {result ? (
          <div className="grid gap-6">
            <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-lg font-semibold text-slate-950">智能体最终回答</h2>
                <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
                  {answerSourceLabel(result.answer_source)}
                </span>
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                  {result.llm_used ? "已启用 LLM" : "未启用 LLM / 使用兜底"}
                </span>
              </div>
              <p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-slate-800">
                {result.answer}
              </p>
              {result.llm_error ? (
                <p className="mt-3 text-xs text-slate-500">LLM 状态：{result.llm_error}</p>
              ) : null}
            </section>

            <EvaluationPanel evaluation={result.evaluation} />

            <PlanViewer steps={result.plan?.steps} routeType={result.route?.type} />

            <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-950">工具结果摘要</h2>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                {result.tool_results?.map((toolResult, index) => (
                  <ToolResultCard
                    key={`${toolResult.tool_name || toolResult.tool}-${index}`}
                    toolResult={toolResult}
                  />
                ))}
              </div>
            </section>

            <TraceViewer trace={result.trace} routeType={result.route?.type} />
          </div>
        ) : null}
      </section>
    </main>
  );
}
