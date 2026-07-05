# Deployment Guide

This project is designed to run without external production systems. The default mode is `LLM_ENABLED=false`, so no API key is required for local demos, CI, or Docker startup.

## Local Python Startup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

## Docker Startup

```bash
docker build -t rd-agent-copilot-api .
docker run --rm -p 8000:8000 \
  -e LLM_ENABLED=false \
  -e DATABASE_URL=sqlite:///data/runs.db \
  rd-agent-copilot-api
```

## Docker Compose Startup

```bash
docker compose up --build
```

Default services:

- API: `http://localhost:8000`
- Web: `http://localhost:3000`

The compose file keeps environment variable examples in `environment` and does not require a local `.env` file. Real keys should only live in a local `.env`, never in source control or Docker images.

## Environment Variables

Core backend:

```bash
DATABASE_URL=sqlite:///data/runs.db
LLM_ENABLED=false
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-v4-flash
LLM_BASE_URL=https://api.deepseek.com
RATE_LIMIT_ENABLED=true
```

Optional provider settings:

```bash
LLM_API_KEY=
DEEPSEEK_API_KEY=
LLM_TIMEOUT_SECONDS=15
LLM_RETRY_COUNT=1
LLM_DAILY_TOKEN_LIMIT=100000
```

## Fallback Mode

With `LLM_ENABLED=false`, the system still runs the full backend chain:

```text
Router -> Planner -> Executor -> Tools/RAG -> Trace -> Answer Synthesizer fallback
```

This is the recommended demo and CI mode because it requires no network access and no API key.

## Common Troubleshooting

- `ModuleNotFoundError: apps`: rebuild the image after Dockerfile changes; the backend imports compatibility modules from `apps/`.
- `database is locked`: stop duplicate local servers or delete only local demo SQLite files after confirming no important run history is needed.
- `429 RATE_LIMITED`: lower request frequency or set `RATE_LIMIT_ENABLED=false` for local load testing.
- `PROVIDER_TIMEOUT`: keep fallback enabled; check provider base URL, timeout, and network connectivity.
- `Docker command not found`: enable Docker Desktop WSL integration or run Docker commands on a host with Docker installed.
- Missing API key: leave `LLM_ENABLED=false` for fallback mode, or set a local uncommitted `.env`.
