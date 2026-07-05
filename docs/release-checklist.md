# Release Checklist

Use this checklist before creating a release tag.

## Validation

- [ ] Run `pytest -q`.
- [ ] If frontend files changed, run `cd apps/web && npm run lint`.
- [ ] If frontend files changed, run `cd apps/web && npm run typecheck`.
- [ ] Run `docker compose config` on a host with Docker installed.
- [ ] Build Docker images when the environment supports it: `docker compose build`.

## Security

- [ ] No API keys committed.
- [ ] No real production logs committed.
- [ ] No real company data committed.
- [ ] `.env` is ignored.
- [ ] `.env.example` contains only empty or safe example values.
- [ ] Artifacts and examples are sanitized.

## Runtime

- [ ] `LLM_ENABLED=false` fallback works.
- [ ] README startup commands are still accurate.
- [ ] Docker Compose starts API and web services.
- [ ] Demo data remains reproducible.
- [ ] `/health` returns healthy config status.
- [ ] Unified error responses do not expose Python tracebacks.

## GitHub

- [ ] PR is reviewed or self-reviewed.
- [ ] CI checks pass.
- [ ] PR is merged.
- [ ] Main branch is pulled locally after merge.
- [ ] Consider creating a release tag, for example `v0.9.0`, after validating the merged main branch.
- [ ] Draft release notes summarize user-facing changes, operational changes, tests, and known limitations.
