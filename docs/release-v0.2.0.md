# Release v0.2.0 Checklist

## Completed Features

- Backend Agent MVP
- Local Tools
- Local RAG
- LangGraph Execution
- DeepSeek Answer Synthesizer
- Trace Viewer
- API Adapter
- Trace Persistence
- Evaluation v1
- Docker Compose
- CI
- Final Demo Docs

## Not Included

- 没有接真实企业日志平台
- 没有接真实配置中心
- 没有真实多用户权限
- 没有生产级部署
- 没有 LoRA 微调

## Acceptance Checklist

- [ ] `python -m pytest` 通过
- [ ] `cd apps/web && npm run lint` 通过
- [ ] `docker compose config` 通过
- [ ] `/chat` simple_qa 可用
- [ ] `/chat` complex_troubleshooting 可用
- [ ] `/runs` 可查询
- [ ] 前端 Trace Viewer 可展示
- [ ] Evaluation 可展示
- [ ] `.env` 未提交
- [ ] README 完整

## Release Notes

v0.2.0 是第二周最终展示版本，目标是让项目达到可投简历、可本地演示、可在面试中讲清楚的状态。

本版本保持 Agent 主链路边界：

- Router 只分类
- Planner 只规划
- Executor 只执行
- LangGraph 只编排工具节点
- Tools 只读取本地样例数据
- DeepSeek 只用于最终回答生成
- Evaluation 只做回答后的质量评估

当前项目仍是可复现 MVP，不声称真实上线或服务真实企业用户。
