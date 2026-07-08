# Adapter Boundary

R&D Agent Copilot currently uses local adapters and mock API semantics to keep the Agent demo deterministic and safe.

## Current Boundary

- `LocalLogAdapter`, `LocalConfigAdapter`, and `LocalGitAdapter` read local sample data through `MockAPIClient`.
- `MockAPIClient` dispatches in process to local mock services. It does not open sockets or call a real log platform, config center, GitHub, GitLab, or database.
- Tools consume adapter results as evidence. They do not own Router, Planner, Executor, Synthesizer, or Trace decisions.
- RAG reads local knowledge files and records retrieval metadata in tool results and trace.

## Future HttpAdapter

A future production integration can add an `HttpAdapter` behind the same adapter interface:

- `LogAdapter.search_logs`
- `ConfigAdapter.compare_configs`
- `GitAdapter.search_commits`

The rest of the Agent chain should not change when the data source changes. Router, Planner, Executor, and Synthesizer depend on structured evidence contracts, not on a concrete API client.

## External Calls

Real external calls are disabled by default in the current project scope. The default local adapters are the only enabled path for log, config, and Git evidence.

When connecting real systems later, replace only the adapter layer and keep these constraints:

- no LLM-controlled tool selection
- no writes to production systems from tools
- explicit allowlist for endpoints and credentials
- trace every adapter call with source, status, latency, and sanitized error
- keep fallback behavior for adapter failures

This keeps the demo credible without pretending to be connected to production infrastructure.
