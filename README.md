# R-D-Agent-Copilot

研发排障智能助手 / Agent 系统 / 工具调用。

## Day1 MVP

Day1 只实现最小可运行 Agent 闭环：

User -> Router -> Planner -> Executor -> Tools -> Trace -> Response

当前范围：

- `POST /chat`
- 规则 Router：`simple_qa` / `complex_troubleshooting`
- Planner：简单问答单步计划，复杂排障三步计划
- Mock Tools：`log_tool`、`config_tool`、`git_tool`
- Executor：按 Planner 步骤调用工具
- Trace：每次请求返回完整内存 Trace

Day1 不包含 LangGraph、RAG、真实 LLM、前端、数据库、Redis 或外部 API。

## Run

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Test

```bash
python -m pytest
```

## Example

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"为什么订单接口报500？"}'
```
