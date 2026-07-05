# Runtime Hardening v1

Runtime Hardening v1 covers the final-answer LLM call only. Router, Planner, Executor, LangGraph tool execution, local tools, and RAG retrieval remain deterministic and do not delegate tool choice to an LLM.

## Why Provider Resilience Matters

Enterprise AI applications depend on third-party model providers that can fail because of network latency, provider-side throttling, regional incidents, SDK errors, or quota exhaustion. A troubleshooting assistant must still return a controlled answer when the model call is unavailable.

This project handles provider risk with:

- Request timeout from environment configuration.
- Retry with exponential backoff.
- A local circuit breaker that marks the provider degraded after consecutive failures.
- Optional fallback provider routing.
- Rule-based fallback when no model provider is usable.

## Why Token Cost Metrics Matter

Token usage is the basic unit for both cost and capacity planning. Without prompt, completion, total token, and cost metadata, a team cannot explain demo spend, production budget, tenant fairness, or sudden cost spikes.

The runtime records:

- `prompt_tokens`
- `completion_tokens`
- `total_tokens`
- `generation_cost_estimate`
- `daily_token_usage`
- `daily_token_limit_exceeded`

When a provider response does not include usage data, the system estimates tokens from character count. This keeps the trace complete without depending on one provider's response shape.

## Why Fallback Is Important

Fallback is useful in demos because the project remains runnable without real API keys and without external network access. It is useful in production because provider outages should degrade the answer quality, not break the entire Router -> Planner -> Executor -> Trace -> Synthesizer response chain.

The rule-based fallback only uses route, plan, local tool results, retrieved knowledge, and trace context. It does not invent facts outside available evidence.

## Environment Variables

```bash
DEEPSEEK_API_KEY=
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-v4-flash
LLM_BASE_URL=https://api.deepseek.com
LLM_ENABLED=false

LLM_TIMEOUT_SECONDS=15
LLM_RETRY_COUNT=1
LLM_RETRY_BACKOFF_SECONDS=0.2
LLM_CIRCUIT_BREAKER_FAILURE_THRESHOLD=3
LLM_CIRCUIT_BREAKER_RESET_SECONDS=60
LLM_DAILY_TOKEN_LIMIT=100000

LLM_FALLBACK_PROVIDER=
LLM_FALLBACK_MODEL=
LLM_FALLBACK_BASE_URL=
LLM_FALLBACK_API_KEY=

RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW_SECONDS=60
```

Security rule: real API keys belong only in local `.env`. Do not commit keys, print keys, or include keys in traces.

## Trace Metadata

The synthesizer trace provider metadata includes:

- `timeout_ms`
- `retry_count`
- `provider_status`
- `fallback_provider_used`
- `circuit_open`
- `prompt_tokens`
- `completion_tokens`
- `total_tokens`
- `generation_cost_estimate`
- `daily_token_usage`
- `daily_token_limit`
- `daily_token_limit_exceeded`

Evaluation v2 aggregates these fields into provider metrics for reporting.

## Interview Talking Points

- "LLMs are not treated as control-plane components. Router, Planner, Executor, and tool selection stay deterministic."
- "The final-answer model call is wrapped with timeout, retry, circuit breaker, fallback provider, and rule-based fallback."
- "Every request still returns a complete trace, even when the provider is disabled, missing a key, degraded, or over token budget."
- "Token and cost metrics are part of trace and evaluation, so runtime spend is observable instead of hidden inside provider logs."
- "The demo remains safe because `LLM_ENABLED=false` is the default and tests never call a real provider."
