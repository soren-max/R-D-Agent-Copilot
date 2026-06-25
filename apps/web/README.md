# R&D Agent Copilot Web

Trace Viewer 前端工程骨架，基于 Next.js、TypeScript 和 TailwindCSS。

当前 PR 只包含静态页面和 API base URL 配置占位，暂不调用后端 `/chat`。

## 安装依赖

```bash
npm install
```

## 启动开发服务

```bash
npm run dev
```

默认访问：

```text
http://127.0.0.1:3000
```

## 环境变量

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

该变量只用于后续 `/chat` API 集成。不要在前端环境变量中放置 API Key 或任何密钥。
