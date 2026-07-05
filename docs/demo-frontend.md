# R&D Agent Copilot — 前端演示文档

## 启动

```bash
# 后端（项目根目录）
uvicorn main:app --reload --port 8000

# 前端（另一个终端）
cd apps/web && npm run dev
```

打开 http://localhost:3000

---

## 页面路由

| 路由 | 页面 | 说明 |
|------|------|------|
| `/` | Agent Console | 主排障界面，输入问题 → 查看全链路结果 |
| `/runs` | Trace Viewer | Run 历史列表 |
| `/runs/[runId]` | Run Detail | **演示重点** — 单条 Run 全链路详情 |
| `/evaluation` | Evaluation 仪表盘 | 评估指标总览 |
| `/knowledge` | Knowledge Base | 知识库管理 |
| `/safety` | Safety Guard | 安全防护控制台 |
| `/settings` | Settings | 系统设置 |

---

## 面试演示顺序（Run Detail 页面）

### 1. 提交排障问题

在 Agent Console（首页）输入：

```
为什么订单接口报500？配置改了但没有生效，应该怎么排查？
```

点击「开始排查」。观察：
- 顶部 Metrics Bar：Intent / Tool Calls / Quality Score / Answer Source
- 右侧 Agent Pipeline：Router → Planner → LangGraph → Synthesizer → Evaluation 逐步完成
- 回答卡片展示最终排障报告

### 2. 进入 Run Detail

左侧 Sidebar 点击 **Trace Viewer** → 点击任意一条 Run → 进入 `/runs/[runId]`。

### 3. 查看 Final Report

**FinalReportCard** 展示：
- `summary` — 排障摘要
- `root_cause` — 初步根因
- `evidence` — 支撑证据列表
- `fix_steps` — 建议修复步骤
- `confidence` — 整体置信度
- `risks` — 风险提示（包括 Incident Memory 仅作历史参考的说明）

### 4. 查看 Trace Timeline

**TraceTimeline** 展示每个执行阶段：
- stage name / icon / 颜色编码
- status badge（success / error / pending）
- latency_ms
- engine（langgraph / deepseek / rule_based）
- tool names 标签
- 点击展开查看 input_summary、output_summary
- Executor stage 显示所有 Persisted Tool Calls 及各自的 status / latency / error

### 5. 查看 Context Metadata

**ContextMetadataCard** 展示：
- `total_chars_before` / `total_chars_after` — 上下文压缩前后字符数
- `compression_ratio` — 压缩率
- `reduced_sections` — 裁剪的 section 数
- `current_query_preserved` — 当前查询是否保留
- `memory_hit_count` — 记忆命中次数

### 6. 查看 Incident Memory

**IncidentMemoryCard** 展示：
- `memory_hit_count` — 总命中次数
- `fresh_count` / `weak_count` / `stale_count` — 新鲜度分布
- 每条记忆条目：query / match_reason / freshness_status / source_run_id
- 底部明确标注：**Incident Memory 是历史参考，不能作为当前证据。**

### 7. 查看 Checkpoint

**CheckpointCard** 展示：
- `status` — checkpoint 状态
- `completed_steps` — 已完成步骤
- `pending_steps` — 待完成步骤
- `last_error` — 最近错误
- `updated_at` — 更新时间
- 操作按钮（当前标注 Demo-only，标注后端接入点 `POST /runs/{runId}/continue`）

### 8. 查看 Evaluation v2

**EvaluationV2Panel** 展示 7 组指标：

| 分组 | 指标示例 |
|------|---------|
| Context | compression_ratio, reduced_sections, memory_hits |
| Tool | tool_success_rate, tool_latency_p50, tool_latency_p99 |
| RAG | retrieval_precision, retrieval_recall, grounding_score |
| Memory | memory_hit_rate, fresh_memory_ratio, stale_memory_ratio |
| Resume | checkpoint_created, stale_checkpoint_count |
| Evidence | evidence_count, avg_confidence, grounding_status |
| Provider | prompt_version, fallback_used, schema_valid, llm_enabled |

### 9. 查看 Provider Metadata

**ProviderMetadataCard** 展示：
- `prompt_version` / `model_provider` / `model_name`
- `llm_enabled` / `fallback_used` / `schema_valid`
- `generation_latency_ms` / `timeout_ms` / `retry_count`
- `provider_status` / `fallback_provider_used` / `circuit_open`
- `prompt_tokens` / `completion_tokens` / `total_tokens`
- `daily_token_usage` / `daily_token_limit_exceeded`
- `provider_error_code` / `provider_error_message`

---

## 面试回答要点

| 面试官问 | 回答 |
|----------|------|
| 为什么不用 LLM 做 Router？ | 确定性、零成本、零延迟。规则 0.1ms 搞定，LLM 需要 1-2s。 |
| RAG 怎么防幻觉？ | Grounding Guard：检索为空或分数低时标记 insufficient_evidence，不调用 LLM。 |
| Trace 有什么用？ | 每个 stage 有 status/latency/input/output/tool_calls，可展开查看。 |
| Evaluation 有几个维度？ | v2 有 7 组：Context/Tool/RAG/Memory/Resume/Evidence/Provider。 |
| Safety 能挡住什么？ | Prompt Injection、高危命令（rm -rf / DROP TABLE）、Secret Masking。 |
