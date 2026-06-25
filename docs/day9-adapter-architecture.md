# Day9 Adapter Architecture

## 1. Day9 Goal

Day9 引入 API Adapter 层，目的是将工具调用与具体数据来源解耦。

当前系统仍使用本地 `LocalAdapter`，保证 demo 可复现、测试可稳定运行。后续可以在不改动 Agent 主链路的前提下，将 Adapter 替换成真实日志平台、配置中心、Git 平台 API。

## 2. Before / After

Before:

```text
log_tool -> data/logs/order-service.log
config_tool -> data/configs/dev.json / prod.json
git_tool -> data/git/commits.json
```

After:

```text
log_tool -> LogAdapter -> LocalLogAdapter -> data/logs/order-service.log
config_tool -> ConfigAdapter -> LocalConfigAdapter -> data/configs/dev.json / prod.json
git_tool -> GitAdapter -> LocalGitAdapter -> data/git/commits.json
```

## 3. Adapter Responsibility

Adapter 层负责：

- 封装数据访问
- 屏蔽 mock 数据和真实 API 的差异
- 返回统一 `AdapterResult`
- 支持未来扩展真实 API 实现

Adapter 层不负责：

- Router 分类
- Planner 规划
- LangGraph 编排
- RAG 检索
- DeepSeek 回答生成
- 用户最终回答

## 4. Current Implementations

当前实现包括：

- `LocalLogAdapter`：读取 `data/logs/order-service.log`，返回日志检索摘要。
- `LocalConfigAdapter`：读取 `data/configs/dev.json` 和 `data/configs/prod.json`，返回配置差异摘要。
- `LocalGitAdapter`：读取 `data/git/commits.json`，返回相关提交摘要。

这些 Adapter 只访问本地确定性样例数据，不调用真实外部 API，不调用 LLM。

## 5. Future Implementations

后续可以预留真实系统接入实现：

- `RealLogAPIAdapter`
- `RealConfigCenterAdapter`
- `RealGitAPIAdapter`

未来可以通过配置切换 adapter provider，例如：

```bash
ADAPTER_PROVIDER=local
ADAPTER_PROVIDER=real_api
```

当前 Day9 不实现真实 API provider，只做架构预留。真实 API 接入必须继续遵守 Router、Planner、Executor、LangGraph、Trace 和 Answer Synthesizer 的职责边界。

## 6. Why This Matters

API Adapter 层的企业级价值：

- 降低工具层和数据源耦合
- 方便替换真实日志平台、配置中心和 Git 平台
- 保持 Agent 主链路稳定
- 支持单元测试和本地演示
- 避免 demo 代码污染生产设计

这使项目不只是本地 mock demo，而是具备清晰企业系统扩展边界的 Agent MVP。

## 7. Interview Explanation

项目初期我使用本地 mock 数据保证可复现，但没有让 tools 永久绑定本地文件。第二周我引入了 API Adapter 层，把 log、config、git 的数据访问抽象出来。当前实现是 LocalAdapter，后续可以替换为真实日志平台、配置中心和 Git 平台 API，而不需要改动 Router、Planner、LangGraph 和前端 Trace Viewer。这让项目从简单 demo 变成了具备企业系统扩展边界的 MVP。
