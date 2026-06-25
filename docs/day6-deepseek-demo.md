# Day6 DeepSeek Demo 与验收清单

## 1. Day6 目标

Day6 的目标是把 DeepSeek API 接入最终回答生成器 Answer Synthesizer，用于把已有工具结果、RAG 文档和 trace 摘要组织成更自然的中文排障报告。

DeepSeek 只用于 Answer Synthesizer，不控制 Router、Planner 和 Tool Calling。Router 仍只负责意图分类，Planner 仍只生成确定性 steps，Executor 和 LangGraph 仍按 Planner 输出执行本地工具。

## 2. 配置方式

先复制示例配置：

```bash
cp .env.example .env
```

默认配置中 LLM 关闭：

```bash
LLM_ENABLED=false
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-v4-flash
LLM_BASE_URL=https://api.deepseek.com
DEEPSEEK_API_KEY=
```

需要启用 DeepSeek 时，填写：

```bash
LLM_ENABLED=true
DEEPSEEK_API_KEY=your_key_here
```

不要把真实 API Key 写入代码、文档示例或提交到仓库。

## 3. 本地运行

安装依赖：

```bash
pip install -r requirements.txt
```

启动服务：

```bash
uvicorn main:app --reload
```

可选运行 demo 脚本：

```bash
python scripts/demo_day6.py
```

## 4. Demo Case 1：LLM 关闭

请求：

```json
{
  "query": "为什么订单接口报500？"
}
```

预期：

- `answer_source = fallback`
- `llm_used = false`
- `llm_error = llm_disabled`
- trace 中 `synthesizer.engine = fallback`
- trace 中 `executor.engine = langgraph`
- 工具调用仍然来自 LangGraph，不由 DeepSeek 决定

验收示例：

```json
{
  "answer_source": "fallback",
  "llm_used": false,
  "llm_error": "llm_disabled",
  "trace": {
    "steps": [
      {
        "stage": "executor",
        "engine": "langgraph"
      },
      {
        "stage": "synthesizer",
        "engine": "fallback",
        "llm_used": false
      }
    ]
  }
}
```

## 5. Demo Case 2：LLM 开启

请求：

```json
{
  "query": "为什么订单接口报500？"
}
```

预期：

- `answer_source = llm`
- `llm_used = true`
- `llm_error = null`
- trace 中 `synthesizer.engine = deepseek`
- 工具调用仍然来自 LangGraph
- Router、Planner、Tool Selection 不受 DeepSeek 控制

验收示例：

```json
{
  "answer_source": "llm",
  "llm_used": true,
  "llm_error": null,
  "trace": {
    "steps": [
      {
        "stage": "executor",
        "engine": "langgraph",
        "graph_name": "tool_execution_graph"
      },
      {
        "stage": "synthesizer",
        "engine": "deepseek",
        "llm_used": true
      }
    ]
  }
}
```

## 6. fallback 策略

如果 API Key 缺失、网络错误、模型调用失败，系统自动回退到 rule-based answer，不影响 `/chat` 可用性。

fallback 时可通过响应字段和 trace 观察：

- `answer_source = fallback`
- `llm_used = false`
- `llm_error` 记录失败原因，例如 `llm_disabled`、`missing_api_key` 或异常类型
- `trace.synthesizer.engine = fallback`
- `trace.executor.engine = langgraph`

这个策略保证 DeepSeek 只增强最终表达，不影响主链路稳定性。

## 7. 面试讲解话术

我没有让大模型直接控制整个 Agent 流程，而是先通过确定性的 Router、Planner、LangGraph 工具编排建立稳定主链路。DeepSeek API 只接入最终 Answer Synthesizer，用于把工具结果和 RAG 证据组织成更自然的中文排障报告。这样既能利用大模型语言生成能力，又避免模型幻觉影响工具选择和执行流程。

## 验收清单

- [ ] `.env` 默认 `LLM_ENABLED=false`
- [ ] 不提交真实 `DEEPSEEK_API_KEY`
- [ ] LLM 关闭时 `/chat` 返回 `answer_source=fallback`
- [ ] LLM 关闭时 `trace.synthesizer.engine=fallback`
- [ ] LLM 开启并配置 API Key 时 `/chat` 返回 `answer_source=llm`
- [ ] LLM 开启时 `trace.synthesizer.engine=deepseek`
- [ ] API Key 缺失时 `/chat` 不崩溃
- [ ] 模型调用失败时 `/chat` 自动 fallback
- [ ] `trace.executor.engine=langgraph`
- [ ] DeepSeek 不参与 Router、Planner 或 Tool Selection
