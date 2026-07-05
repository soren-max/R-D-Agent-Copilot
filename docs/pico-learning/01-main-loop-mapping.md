# 01 Main Loop Mapping

本篇记录 Pico 主链路和 R&D Agent Copilot 主链路的对应关系，用于后续逐章迁移。

## Pico 主链路

```text
CLI
-> Runtime
-> Context
-> Model
-> Tool
-> Memory
-> Trace
-> Report
```

可以理解为：

- CLI 接收用户任务和运行参数。
- Runtime 驱动 Agent 主循环。
- Context 组织当前任务、环境、历史和工具结果。
- Model 基于上下文生成下一步动作或最终输出。
- Tool 执行受控操作。
- Memory 保存长期或跨轮状态。
- Trace 记录执行过程。
- Report 汇总结果，方便用户 review。

## 本项目主链路

```text
Chat API
-> Router
-> Planner
-> LangGraph Executor
-> Tools / RAG
-> Trace
-> Answer Synthesizer
-> Evaluation
```

当前 R&D Agent Copilot 的主链路更偏后端服务：

- Chat API 接收 `/chat` 请求。
- Router 只做意图分类：`simple_qa` 或 `complex_troubleshooting`。
- Planner 只生成结构化排查计划。
- LangGraph Executor 只执行 Planner 输出。
- Tools / RAG 读取本地确定性样例和本地知识库。
- Trace 记录 router、planner、executor、synthesizer 等阶段。
- Answer Synthesizer 基于已有 route、plan、tool_results 和 trace 生成最终中文回答。
- Evaluation 在回答后做 rule-based 质量评估。

## 模块映射表

| Pico 模块 | Pico 职责 | 本项目对应模块 | 本项目职责 | 当前状态 |
| --- | --- | --- | --- | --- |
| CLI | 接收任务、参数和运行入口 | Chat API | 接收 `/chat` 请求并返回结构化响应 | 已有 |
| Runtime | 驱动 Agent 主循环 | Pipeline | 串联 Router、Planner、Executor、Synthesizer、Evaluation | 已有 |
| Context | 组织 prompt、工具结果、历史和预算 | Context Manager | 构建分层 `ContextPackage`，压缩 evidence/history | 升级中 |
| Model | 生成下一步或最终输出 | Answer Synthesizer / DeepSeek | 只生成最终中文回答，不控制工具 | 已有 |
| Tool | 受控执行环境操作 | Tools / RAG | 执行 log/config/git/RAG 本地查询 | 已有 |
| Tool Gateway | 工具白名单、权限和安全边界 | Safety Tool Policy / Executor Boundary | 校验工具计划，不接真实生产 API | 部分已有 |
| Memory | 保存跨轮上下文和历史经验 | Incident Memory | 保存历史故障、证据链、处理结果 | 待建设 |
| Trace | 记录执行过程和状态 | Trace System | 记录 stage、latency、tool calls、LLM usage、metadata | 已有 |
| Checkpoint | 中断后恢复执行 | Checkpoint Resume | 保存执行状态并恢复未完成 run | 待建设 |
| Report | 输出用户可读总结 | Answer / Evaluation / Evidence Chain | 输出中文排障报告、质量评分和证据链 | 已有 |

## 关键差异

Pico 的 Model 往往会参与 coding loop 中的下一步动作生成。

本项目当前阶段不采用这种方式。DeepSeek 只允许用于最终 Answer Synthesizer，不能控制 Router、Planner 或 Tool Selection。工具执行链必须保持：

```text
Router
-> Planner
-> LangGraph Executor
-> Tools / RAG
```

这能保证排障 Agent 在 demo 和测试中稳定、可追踪、可回退。

## 下一步升级方向

### Context Manager

把 prompt、工具证据、RAG evidence 和 run history 组织为分层 `ContextPackage`。重点是预算控制、不可裁剪的当前 query、压缩 metadata 和 trace 可回看。

### Tool Gateway

把工具调用边界从“Executor 内部能调用哪些工具”进一步升级为统一网关，包括工具白名单、参数校验、权限策略、失败兜底和审计字段。

### Incident Memory

沉淀历史故障案例、根因候选、证据链和处理建议。它不替代 RAG，也不让 LLM 直接写入可信事实，而是作为排障经验层供后续检索和评估。

### Checkpoint Resume

为较长的排障 run 增加 checkpoint。目标是在工具执行失败、服务重启或用户中断后，可以从已完成 stage 继续，而不是重新跑完整链路。

### Evaluation v2

从当前 rule-based 质量评分升级为更细的评估体系，包括 evidence coverage、trace completeness、answer groundedness、tool usefulness、latency budget 和 bad case replay。

## 面试讲解话术

我没有直接照搬 Pico 的 Coding Agent，而是学习它的 Harness 分层思路。Pico 解决的是代码任务中的主循环、上下文、工具、记忆、trace 和报告问题；我的项目把同样的工程抽象迁移到研发排障场景。

在 R&D Agent Copilot 里，用户请求不会直接交给 LLM，而是先经过 Router、Planner 和 LangGraph Executor，工具只读取本地确定性样例和 RAG 知识库。LLM 只放在最终 Answer Synthesizer，用已有证据组织中文排障报告。这样既能展示 Agent workflow，又能保证工具选择可控、trace 可回看、测试可复现。
