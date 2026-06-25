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

## 本地样例数据说明

Day2 提供一组确定性的本地排障样例数据，作为后续工具系统强化的数据来源：

- `data/logs/order-service.log`：模拟订单接口 500、payment-service timeout、trace_id 和服务名等日志线索。
- `data/configs/dev.json` / `data/configs/prod.json`：模拟不同环境配置差异，包括支付超时、订单重试次数和新支付流程开关。
- `data/git/commits.json`：模拟最近提交记录，包含提交 ID、作者、变更文件、风险等级和中文友好的摘要。

这些数据仅用于本地确定性排障演示，不接入真实外部 API、数据库、RAG 或 LLM。

## Local Knowledge Base

`data/docs/` 存放本地知识库样例文档，覆盖配置中心、服务日志、接口异常排查流程和订单服务 FAQ。Day3 会基于这些文档实现轻量 RAG 检索。当前文档仅用于模拟研发排障场景，不接入外部知识库或真实公司数据。

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
