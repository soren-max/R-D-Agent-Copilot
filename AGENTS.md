# R&D Agent Copilot Agent Rules

This project follows the Day1 Agent MVP contract.

## Required Flow

Every chat request must pass through this chain:

User -> Router -> Planner -> Executor -> Tools -> Trace -> Response

The API must not bypass Router, Planner, Executor, or Tools. Every request must return a complete in-memory trace with a UUID trace ID, stage outputs, stage latency, tool calls, and the final answer.

## Day1 Scope

Day1 is limited to a deterministic backend MVP:

- FastAPI `POST /chat`
- Rule-based Router
- Deterministic Planner
- Deterministic mock Tools
- Executor-driven tool calls
- In-memory Trace returned with the response
- Minimal pytest coverage

Do not add LangGraph, RAG, a real LLM, frontend UI, database storage, Redis, external API calls, or complex evaluation systems in Day1 PRs.

## Component Boundaries

- Router only classifies user input as `simple_qa` or `complex_troubleshooting`.
- Router must not call tools, generate final answers, or decompose tasks.
- Planner only creates plans from `query` and `route_result`.
- Planner must not execute tools or generate final answers.
- Executor only iterates over `plan.steps`, calls the declared tool, and collects tool results.
- Executor must not re-plan, modify planner output, or produce the final answer.
- Tools must be deterministic mocks and must not call LLMs or external APIs.
- Final answers must be Chinese and based on returned tool or executor results.

## PR Discipline

Each PR should solve one clear goal. Day1 acceptance PRs should only touch Day1 backend MVP files and tests.
