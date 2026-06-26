# Day11 Evaluation

## 1. Day11 Goal

Evaluation v1 的目标是衡量一次 Agent 执行质量。它不参与 Router、Planner、Executor 或工具选择，只在回答生成之后读取已有的 route、plan、tool_results、trace 和 answer，输出可解释的质量评分。

## 2. Metrics

- `tool_success_rate`：成功工具数量 / 实际执行工具数量，用于衡量工具链路是否稳定完成。
- `trace_completeness`：检查 trace 是否包含 router、planner、executor、synthesizer 等核心阶段。
- `rag_relevance`：根据 `rag_retriever` 是否命中文档评估知识库补充质量。
- `answer_groundedness`：根据回答是否包含日志、配置、Git、知识库、timeout、500、工具证据等关键词评估证据性。
- `latency_score`：根据总耗时阈值给出响应耗时评分。

## 3. Why Rule-based First

当前不使用 LLM judge，是为了保证测试稳定、结果可解释、无 API 依赖。rule-based 评分可以在本地确定性运行，也便于面试和 demo 时说明每个分数的来源。

后续可以扩展 DeepSeek Judge 或人工评审，将 rule-based 结果作为基础分，再叠加模型评审或人工验收标签。

## 4. Frontend Display

前端在 Agent 回答下方展示 Evaluation v1：

- `overall_score` 显示为百分比和中文等级。
- metrics 展示工具成功率、Trace 完整性、知识库相关性、回答证据性和响应耗时评分。
- issues 展示发现的问题。
- suggestions 展示优化建议。

如果后端暂时没有返回 `evaluation`，前端显示“暂无评估结果”，不会影响回答和 Trace Viewer。

Trace Viewer 如果收到 `evaluation` stage，会在时间线中显示 `Evaluation / 质量评估`，并展示 `engine=rule_based`、`overall_score` 和 `latency_ms`。

## 5. Interview Explanation

“第十一天我加入了 Evaluation v1。这个模块不会参与 Agent 决策，而是在回答生成之后，根据工具成功率、Trace 完整性、RAG 命中、回答证据性和耗时给出质量评分。它的价值是让系统不只是能回答，还能量化回答质量，为后续优化 Prompt、工具调用和知识库提供依据。当前采用 rule-based 方式，保证可解释和可测试，后续可以扩展为 LLM-as-a-Judge 或人工评审。”

## 6. Boundary

Evaluation v1 不替代真实线上评估体系，也不声称能完整判断排障结论是否绝对正确。它当前只基于本地样例工具结果、trace 完整性和回答证据性进行规则评分，目标是为 MVP 提供可解释的质量信号。

后续如果接入真实企业 API，可以增加：

- LLM Judge：对回答是否充分引用证据、建议是否合理进行语义评估。
- Human Review：让研发同学标注是否接受结论。
- Case Regression：把典型故障沉淀成评测集，持续检查 Agent 改动是否退化。
