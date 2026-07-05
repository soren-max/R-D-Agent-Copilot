# Pico Learning and Migration Notes

这个目录用于记录把 Pico Agent Harness 的设计思路迁移到 R&D Agent Copilot 的过程。

目标不是照搬 Pico，也不是把当前项目改成 Coding Agent，而是学习它在 Agent Harness 层面的工程组织方式：主循环、上下文管理、工具边界、记忆、trace、恢复和评估。

## 为什么学习 Pico

Pico 的价值不在于某一个具体工具，而在于它把 Coding Agent 拆成了一套清晰的 Harness：

- Runtime 负责主循环和状态推进。
- Context 负责把任务、代码、工具结果和历史压缩成模型可用输入。
- Tool 层负责受控执行，而不是让模型直接操作环境。
- Memory 和 Trace 负责可恢复、可回看、可评估。
- Report 负责把执行过程和结果沉淀为人能理解的输出。

这些能力和本项目的研发排障场景高度相似。R&D Agent Copilot 也需要一个可控、可测试、可追踪、可回放的 Agent Harness，而不是一个简单聊天接口。

## Pico 和本项目的定位差异

Pico 是 Coding Harness。

它面向代码任务，核心问题是：如何让 Agent 在代码仓库中读取上下文、规划修改、调用工具、执行验证，并把过程可靠地记录下来。

R&D Agent Copilot 是 R&D Troubleshooting Agent Harness。

它面向研发排障任务，核心问题是：如何让 Agent 对用户故障问题进行分类、规划排查步骤、执行本地工具和 RAG 检索、记录 trace、生成中文排障报告，并用 Evaluation 和 Evidence Chain 评估回答质量。

两者的业务对象不同，但 Harness 思路可以迁移：

- Pico 的 code context 对应本项目的 incident context。
- Pico 的 coding tools 对应本项目的 log/config/git/RAG tools。
- Pico 的 execution trace 对应本项目的 full trace 和 stage metadata。
- Pico 的 report 对应本项目的 Answer Synthesizer、Evaluation 和 Evidence Chain。

## 学习方式

采用小步迁移，不一次性重写主流程。

1. 学一章

   先理解 Pico 某一章解决的 Harness 问题，例如 main loop、context、tool gateway、memory、checkpoint 或 evaluation。

2. 映射到项目

   把 Pico 的模块映射到 R&D Agent Copilot 的现有链路，明确哪些已经有，哪些是缺口，哪些不适合当前阶段做。

3. 小步 PR

   每次只改一个清晰目标，例如新增 Context Manager、整理 Tool Gateway 边界、增加 Incident Memory 文档或补充 trace metadata。

4. 测试

   每一步都保留当前默认 `LLM_ENABLED=false` 的可运行能力，并用 pytest 验证主链路不被破坏。

5. 面试话术

   每完成一章迁移，都沉淀一段可讲解的话术：为什么这样设计、解决了什么工程问题、如何保证安全和可回退。

## 当前迁移原则

- 不让 LLM 控制 Router、Planner 或 Tool Selection。
- 不绕过 LangGraph Executor。
- 不接真实生产系统 API。
- 不引入数据库、Redis 或前端大改，除非项目进入对应阶段。
- 不提交真实 API Key。
- 保持每次改动小模块、可测试、可回滚。
