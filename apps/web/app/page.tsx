import { AppHeader } from "@/components/app-header";
import { EmptyState } from "@/components/empty-state";

const modules = [
  {
    title: "对话输入区",
    description: "后续用于输入研发问题，例如订单接口 500、配置差异或知识库问答。",
    items: ["用户问题输入", "提交到 /chat", "展示请求状态"],
  },
  {
    title: "Agent 执行结果区",
    description: "后续展示 Router、Planner、Tools、RAG 和 Answer Synthesizer 返回的中文结果。",
    items: ["最终回答", "工具结果摘要", "大模型回退状态"],
  },
  {
    title: "Trace 执行链路区",
    description: "后续展示 router、planner、executor、synthesizer 的完整执行链路。",
    items: ["LangGraph 工具调用", "跳过节点", "重试 / 回退"],
  },
];

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50">
      <AppHeader />
      <section className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-5 py-8 sm:px-8 lg:px-10">
        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <p className="max-w-3xl text-sm leading-6 text-slate-700">
            输入研发问题后，系统会经过 Router、Planner、LangGraph Tool Nodes 和 Answer Synthesizer
            生成可追踪回答。
          </p>
        </div>

        <div className="grid gap-5 lg:grid-cols-3">
          {modules.map((module) => (
            <EmptyState
              key={module.title}
              title={module.title}
              description={module.description}
              items={module.items}
            />
          ))}
        </div>
      </section>
    </main>
  );
}
