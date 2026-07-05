# R&D Agent Copilot — 前端演示文档

## 启动

```bash
# 后端
uvicorn main:app --reload --port 8000

# 前端（另一个终端）
cd apps/web
npm run dev
```

打开 http://localhost:3000

---

## 面试演示顺序

### 1. 提交排障问题

在 Agent Console 输入：

```
为什么订单接口报500？配置改了但没有生效，应该怎么排查？
```

点击「开始排查」，观察 Agent Pipeline 逐步完成 Router → Planner → Executor → Synthesizer → Evaluation。

### 2. 查看最终报告

回答卡片展示 final report：

- summary / root_cause
- evidence 列表
- fix_steps
- confidence
- risks

### 3. 查看 Trace

切换到 Trace Viewer（左侧 Sidebar → Trace Viewer）。

或直接点击 Run 进入 `/runs/[runId]`。

Timeline 展示：

- 每个 stage 的名称 / icon / 颜色
- status（success / error / pending）
- latency_ms
- engine
- output 摘要

### 4. 查看 Context Metadata

Context Metadata 卡片展示：

- total_chars_before / after
- compression_ratio
- reduced_sections
- current_query_preserved
- memory_hit_count

### 5. 查看 Incident Memory

Incident Memory 卡片展示：

- memory_hit_count
- fresh / weak / stale 计数
- 每条记忆的 query / match_reason / freshness_status
- 明确标注「Incident Memory 是历史参考，不能作为当前证据」

### 6. 查看 Checkpoint

Checkpoint 卡片展示：

- status
- completed_steps / pending_steps
- last_error
- updated_at
- 操作按钮（UI 占位）

### 7. 查看 Evaluation v2

Evaluation v2 面板展示 7 组指标：

- Context
- Tool
- RAG
- Memory
- Resume
- Evidence
- Provider

### 8. 查看 Provider Metadata

Provider Metadata 卡片展示：

- prompt_version
- model_provider / model_name
- llm_enabled
- fallback_used
- schema_valid
- generation_latency_ms
- provider_error_code

---

## 页面路由

| 路由 | 页面 | 说明 |
|------|------|------|
| `/` | Agent Console | 主排障界面 |
| `/runs` | Trace Viewer | Run 列表 |
| `/runs/[runId]` | Run Detail | 单条 Run 全链路详情 |
| `/evaluation` | Evaluation 仪表盘 | 评估指标 |
| `/knowledge` | Knowledge Base | 知识库管理 |
| `/safety` | Safety Guard | 安全防护 |
| `/settings` | Settings | 系统设置 |
