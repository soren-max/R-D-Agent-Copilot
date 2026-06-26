# Interview Script

## 30 秒版本

R&D Agent Copilot 是一个面向研发排障场景的 AI Agent MVP。它不是普通聊天套壳，而是把一次用户请求拆成 Router、Planner、LangGraph Executor、Tools / RAG、Trace、Answer Synthesizer 和 Evaluation。系统可以回答配置中心这类知识问题，也可以模拟排查订单接口 500，通过日志、配置、Git 变更和知识库证据生成中文排障报告。

## 1 分钟版本

这个项目解决的是研发排障中信息分散、链路长、结论难复现的问题。后端用 FastAPI 暴露 `/chat`，请求先进入 Router 判断 simple_qa 或 complex_troubleshooting，再由 Planner 生成结构化步骤。Executor 内部使用 LangGraph 编排工具节点，调用本地 log、config、git 和 rag 工具收集证据。Trace 会记录每个阶段的输出、耗时、工具调用、跳过节点和 fallback 状态。DeepSeek 只作为最终 Answer Synthesizer，可选生成更自然的中文回答，失败时走 fallback。前端 Trace Viewer 展示执行链路，Evaluation v1 对工具成功率、Trace 完整性、RAG 命中、回答证据性和耗时进行评分。

## 3 分钟版本

我做这个项目的出发点是：真实研发排障往往不是问答问题，而是一个跨系统的证据收集过程。比如接口 500，研发同学需要看日志、配置、最近代码变更和知识库文档。普通 ChatBot 很容易直接生成一个看起来合理的答案，但它不一定知道证据来自哪里，也不方便回溯和评估。

所以我把系统设计成分层 Agent 链路。Router 只负责判断问题类型，Planner 只负责生成结构化计划，Executor 只负责执行计划，不重新规划。工具层通过 Adapter 读取数据，当前是 LocalAdapter，使用本地样例日志、配置、Git 和知识库，保证 demo 和测试稳定。未来如果接真实企业系统，可以替换成 RealLogAPIAdapter、RealConfigCenterAdapter 和 RealGitAPIAdapter。

LangGraph 在这里不是替代 Router 或 Planner，而是在 Executor 内部做工具节点编排。它负责根据 Planner steps 条件执行 log、config、git、rag 节点，记录 skipped nodes、retry、fallback 和节点级 trace。这样可以清楚看到一次请求到底执行了哪些工具，哪些节点被跳过，哪些结果进入最终回答。

DeepSeek 的接入位置也被限制在 Answer Synthesizer。它只基于 route、plan、tool_results 和 trace 生成中文排障报告，不控制 Planner，也不选择工具。这样做是为了让系统更可控：LLM 负责表达，确定性代码负责流程和工具执行。如果 DeepSeek 没有配置 API Key 或调用失败，系统会自动使用 fallback answer，测试也不会依赖真实 LLM。

Trace 和 Evaluation 是这个项目的另一个重点。Trace 让每次 Agent 执行可观察，前端 Trace Viewer 可以展示 Router、Planner、Executor、Synthesizer 和 Evaluation 的完整链路。Evaluation v1 在回答生成后运行，用 rule-based 指标给出质量评分，包括工具成功率、Trace 完整性、RAG 命中、回答证据性和耗时。它不参与决策，只提供质量信号。

当前边界也很明确：项目使用本地样例数据模拟研发排障，不声称真实上线或服务真实企业用户；没有接真实日志平台、配置中心或 Git API；没有生产级权限和部署体系。后续扩展方向是接真实 Adapter、做 Trace 历史页、加入 LLM Judge 或人工 Review，并完善权限控制和部署方案。

## 常见追问

### 1. 这个项目和普通 ChatBot 区别是什么？

普通 ChatBot 通常直接把问题交给模型生成回答。本项目有确定性的 Router、Planner、Executor 和工具链路，回答来自日志、配置、Git 和 RAG 证据，并且有 Trace、持久化和 Evaluation。

### 2. 为什么不用 LLM 直接规划工具？

工具规划会影响执行链路和结果可复现性。如果让 LLM 直接规划工具，测试、回归和错误定位会更难。本项目先用确定性 Planner 保证稳定，再把 LLM 放在最终回答生成阶段。

### 3. LangGraph 在这里解决了什么问题？

LangGraph 负责 Executor 内部工具节点编排，包括条件执行、跳过节点、retry、fallback 和节点级 trace。它让工具执行过程结构化、可观察，但不替代 Router 或 Planner。

### 4. mock 数据会不会太 demo？

当前确实是本地样例数据 MVP，不声称真实生产接入。这样做的价值是让主链路、测试、Trace Viewer 和 Evaluation 都可复现。真实接入时可以替换 Adapter，而不必重写 Agent 主链路。

### 5. 怎么接真实企业系统？

保持 Tool 的输入输出契约不变，把 LocalAdapter 替换为真实 Adapter。真实 Adapter 负责鉴权、请求、超时、错误处理和数据标准化，向上继续返回统一结果。

### 6. Evaluation 是怎么评估的？

Evaluation v1 是 rule-based。它读取回答后的 route、plan、tool_results、trace 和 answer，评估工具成功率、Trace 完整性、RAG 命中、回答证据性和耗时，不参与 Agent 决策。

### 7. DeepSeek 失败怎么办？

DeepSeek 默认关闭。如果没有 API Key、网络异常或模型调用失败，Answer Synthesizer 会回退到 rule-based fallback answer，并在响应和 trace 中记录 `llm_used=false`、`answer_source=fallback` 和错误信息。

### 8. Trace 持久化有什么用？

Trace 持久化让一次 Agent 执行可以被回查。前端和 API 可以查看历史 run、stage、tool call 和 evaluation，方便 demo、调试、回归分析和后续做质量看板。
