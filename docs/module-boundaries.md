# Module Boundaries

This document records the current repository boundary so future cleanup does not accidentally change the Agent runtime path.

## Current Runtime Entry

The backend entrypoint is the repository root `main.py`:

```bash
uvicorn main:app --reload --port 8000
```

`main.py` registers FastAPI routers from `app/api/` and middleware from `app/core/`. A `/chat` request enters `app.api.chat.chat_endpoint`, then runs the Agent chain in `app.agent.pipeline`.

Current main chain:

```text
API
-> Router
-> Planner
-> LangGraph Executor
-> Tool Gateway
-> Tools / RAG
-> Trace
-> Context Manager
-> Answer Synthesizer
-> Evaluation v2
-> Evidence Chain
```

## `app/`

`app/` is the current primary backend runtime package.

- `app/api/`: FastAPI routes for chat, streaming, runs, mock data, and ops endpoints.
- `app/agent/`: Router, Planner, Executor, LangGraph orchestration, streaming, pipeline, and Answer Synthesizer.
- `app/core/`: config, logging, errors, responses, rate limit, LLM client, models, and trace contracts.
- `app/tools/`: Tool Gateway, tool registry, policies, and local tool implementations.
- `app/adapters/`: local adapters that isolate mock logs, configs, and git data behind stable contracts.
- `app/rag/`: current local RAG ingestion, vector store, retriever, and embedding helpers used by backend tests and retrieval paths.
- `app/eval/`: Evaluation v2 schemas, metrics, reports, artifact aggregation, and legacy v1-compatible helpers.
- `app/evidence/`: Evidence Chain builder and confidence scoring.
- `app/memory/`: Incident Memory storage, retrieval, and freshness logic.
- `app/resume/`: Checkpoint / Resume state and drift handling.
- `app/persistence/`: SQLite-backed run, step, and tool-call persistence.
- `app/observability/`: health/config checks, trace export, and evaluation report helpers.
- `app/llms/` and `app/prompts/`: provider and prompt assets for the final Answer Synthesizer. Router and Planner do not call LLM providers.

## `apps/web/`

`apps/web/` is the frontend Trace Viewer.

It displays chat output, run detail, trace timeline, evidence, context metadata, provider metadata, checkpoint/resume state, and evaluation panels. It is not part of the backend control plane and should not contain API keys.

## `apps/api/app/`

`apps/api/app/` is not the current FastAPI application entrypoint. It is a compatibility and migration package kept from earlier monorepo layout work.

Current status:

- `apps/api/app/context/`: active compatibility module. The backend imports `ContextManager`, `ContextPackage`, sections, reducers, and metadata from here. It should be migrated into `app/` later in a dedicated PR.
- `apps/api/app/rag/`: active compatibility/experimental RAG module. The backend uses keyword retrieval, grounding checker, provider fallback helpers, and local KB loaders from here. RAG Pipeline v2 docs and tests also cover these helpers.
- `apps/api/app/safety/`: active compatibility safety module. The backend uses prompt injection detection and tool-policy validation from here.
- `apps/api/app/kb/`: local demo knowledge-base documents. These are sanitized sample docs, not production data.
- `apps/api/app/llms/` and `apps/api/app/prompts/`: legacy compatibility copies. The current final-answer provider path uses `app/llms/` and `app/prompts/`; Router and Planner remain deterministic.

Do not delete `apps/api/app/` wholesale until imports have been migrated and tests prove the main chain no longer depends on it.

## Directory Cleanup Roadmap

Keep cleanup incremental:

1. Move `apps/api/app/context/` into `app/context/`, update imports, and keep tests green.
2. Consolidate RAG modules by choosing one canonical package under `app/rag/`, then migrate `apps/api/app/rag/` helpers in small PRs.
3. Move safety helpers into `app/safety/` or `app/tools/policies.py` depending on ownership.
4. Remove legacy `apps/api/app/llms/` and `apps/api/app/prompts/` only after no imports or docs reference them as active paths.
5. Keep `apps/web/` unchanged unless a frontend task explicitly requires it.

Each cleanup PR should update this document, run `pytest -q`, and avoid changing Router, Planner, Executor, or Answer Synthesizer behavior unless that PR is explicitly scoped to runtime code.
