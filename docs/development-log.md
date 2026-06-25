# Development Log

## Day1：Agent MVP

完成最小可运行 Agent 闭环：`POST /chat`、Router、Planner、Executor、Tools、Trace、Response。
所有回答基于确定性工具结果生成，保持 Day1 后端 MVP 范围。

## Day2：Local troubleshooting tools

引入本地日志、配置和 Git 提交样例数据。
实现 `log_tool`、`config_tool`、`git_tool`，用于模拟研发排障证据收集。

## Day3：Local RAG

新增 `data/docs/` 本地知识库样例文档。
实现轻量本地检索能力，让 simple QA 和 complex troubleshooting 都能获得知识库补充。

## Day4：LangGraph execution layer

在 Executor 内部接入 LangGraph 执行层。
Router 和 Planner 保持确定性实现，LangGraph 只负责工具节点编排。

## Day5：Conditional execution / retry / fallback

支持根据 Planner steps 条件执行工具节点。
补充失败 retry、fallback、skipped_nodes、tool_calls 和执行 trace 元数据。

## Day6：DeepSeek Answer Synthesizer

新增 LLM 配置和 DeepSeek OpenAI-compatible client。
DeepSeek 只用于 Answer Synthesizer，LLM 不控制 Router、Planner 或 Tool Selection；无 key 或失败时自动 fallback。

## Day7：Regression / docs / release checklist

完成 Week1 全链路回归验收，覆盖 simple QA、复杂排障、LangGraph metadata、RAG、LLM fallback 和安全配置。
补充架构文档、demo guide 和 v0.1.0 release checklist，方便 Week2 开发和面试展示。
