export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export const CHAT_ENDPOINT = `${API_BASE_URL}/chat`;
export const CHAT_STREAM_ENDPOINT = `${API_BASE_URL}/chat/stream`;
export const RUNS_ENDPOINT = `${API_BASE_URL}/runs`;

export type RouteResult = {
  type: "simple_qa" | "complex_troubleshooting" | string;
  confidence?: number;
  reason?: string;
};

export type PlanStep = {
  id: number;
  action: string;
  tool: string;
  description: string;
};

export type PlanResult = {
  plan_type: string;
  steps: PlanStep[];
};

export type ToolResult = {
  tool_name?: string;
  tool?: string;
  status: string;
  confidence: number;
  source: string;
  result: string;
  latency_ms?: number;
  documents?: RagDocument[];
  rag_metadata?: RagMetadata;
};

export type RagDocument = {
  content?: string;
  source?: string;
  title?: string;
  section?: string;
  score?: number;
  chunk_id?: string;
  doc_type?: string;
  updated_at?: string;
  retrieval_type?: string;
};

export type RagMetadata = {
  retrieval_top_k?: number;
  score_threshold?: number;
  retrieved_count?: number;
  grounding_status?: string;
  retrieval_latency_ms?: number;
  retrieval_type?: string;
  fallback_used?: boolean;
  vector_available?: boolean;
};

export type LLMUsage = {
  provider?: string;
  model?: string;
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
  estimated_cost?: number;
  currency?: string;
  latency_ms?: number;
  source?: "api_usage" | "estimated" | "llm_disabled" | "fallback" | string;
};

export type EvidenceItem = {
  id: string;
  type: "log" | "config" | "git" | "rag" | "evaluation" | string;
  source?: string;
  summary: string;
  confidence: number;
  related_tool?: string;
};

export type RootCauseCandidate = {
  title: string;
  confidence: number;
  supporting_evidence_ids?: string[];
  reason: string;
};

export type EvidenceChain = {
  overall_confidence: number;
  root_cause_candidates?: RootCauseCandidate[];
  evidence_items?: EvidenceItem[];
};

export type TraceToolCall = {
  node?: string;
  tool_name?: string;
  status?: string;
  retry_count?: number;
  error?: string;
  latency_ms?: number;
  source?: string;
  retrieval_top_k?: number | null;
  score_threshold?: number | null;
  retrieved_count?: number | null;
  grounding_status?: string;
  retrieval_latency_ms?: number | null;
  retrieval_type?: string;
  fallback_used?: boolean | null;
};

export type TraceSkippedNode = {
  node?: string;
  tool_name?: string;
  reason?: string;
};

export type TraceStep = {
  stage?: string;
  engine?: string;
  graph_name?: string;
  output?: string;
  latency_ms?: number;
  llm_used?: boolean;
  llm_error?: string | null;
  prompt_version?: string;
  tool_calls?: TraceToolCall[];
  skipped_nodes?: TraceSkippedNode[];
  fallback_used?: boolean;
  overall_score?: number | null;
  evaluation_error?: string | null;
  retrieval_top_k?: number | null;
  score_threshold?: number | null;
  retrieved_count?: number | null;
  grounding_status?: string;
  retrieval_latency_ms?: number | null;
  llm_usage?: LLMUsage | null;
};

export type TraceData = {
  trace_id?: string;
  steps?: TraceStep[];
  final_answer?: string;
};

export type EvaluationMetrics = {
  tool_success_rate?: number;
  trace_completeness?: number;
  rag_relevance?: number;
  answer_groundedness?: number;
  latency_score?: number;
  evidence_confidence_score?: number | null;
};

export type LatencyBreakdown = {
  router_ms?: number;
  planner_ms?: number;
  executor_ms?: number;
  tools_ms?: number;
  synthesizer_ms?: number;
  evaluation_ms?: number;
  total_ms?: number;
  bottleneck_stage?: string;
  bottleneck_ms?: number;
};

export type EvaluationResult = {
  overall_score?: number;
  metrics?: EvaluationMetrics;
  latency_breakdown?: LatencyBreakdown;
  issues?: string[];
  suggestions?: string[];
};

export type ChatResponse = {
  run_id?: string;
  answer: string;
  answer_source: "fallback" | "llm" | string;
  llm_used: boolean;
  llm_error?: string | null;
  llm_usage?: LLMUsage | null;
  route: RouteResult;
  plan: PlanResult;
  tool_results: ToolResult[];
  trace?: TraceData;
  evaluation?: EvaluationResult | null;
  evidence_chain?: EvidenceChain | null;
};

export type StreamEventName =
  | "router_started"
  | "router_completed"
  | "planner_started"
  | "planner_completed"
  | "executor_started"
  | "tool_started"
  | "tool_completed"
  | "synthesizer_started"
  | "synthesizer_completed"
  | "evaluation_started"
  | "evaluation_completed"
  | "completed"
  | "error";

export type AgentStreamEvent = {
  event: StreamEventName | string;
  timestamp?: string;
  message?: string;
  tool_name?: string;
  status?: string;
  latency_ms?: number;
  run_id?: string;
  answer?: string;
  evaluation?: EvaluationResult | null;
  response?: ChatResponse;
  llm_usage?: LLMUsage | null;
  error?: string;
};

export type RunSummary = {
  run_id: string;
  query: string;
  route_type?: string | null;
  answer_source?: string | null;
  llm_used?: boolean;
  status?: string | null;
  total_latency_ms?: number | null;
  evaluation_score?: number | null;
  created_at?: string | null;
};

export type PersistedRunStep = {
  stage?: string;
  engine?: string | null;
  input?: Record<string, unknown> | unknown[] | null;
  output?: Record<string, unknown> | unknown[] | null;
  latency_ms?: number | null;
  status?: string | null;
  created_at?: string | null;
};

export type PersistedToolCall = {
  node?: string | null;
  tool_name?: string | null;
  status?: string | null;
  source?: string | null;
  confidence?: number | null;
  retry_count?: number | null;
  error?: string | null;
  latency_ms?: number | null;
  result?: Record<string, unknown> | unknown[] | null;
  created_at?: string | null;
};

export type RunDetail = {
  run: RunSummary;
  steps: PersistedRunStep[];
  tool_calls: PersistedToolCall[];
  evaluation?: EvaluationResult | null;
};

export async function postChat(query: string): Promise<ChatResponse> {
  const response = await fetch(CHAT_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    throw new Error(`Chat request failed: ${response.status}`);
  }

  return response.json();
}

export function chatStreamUrl(query: string): string {
  return `${CHAT_STREAM_ENDPOINT}?query=${encodeURIComponent(query)}`;
}

export async function fetchRuns(limit = 30): Promise<RunSummary[]> {
  const response = await fetch(`${RUNS_ENDPOINT}?limit=${limit}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Runs request failed: ${response.status}`);
  }

  const data = await response.json();
  return data.runs ?? [];
}

export async function fetchRun(runId: string): Promise<RunDetail> {
  const response = await fetch(`${RUNS_ENDPOINT}/${encodeURIComponent(runId)}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Run detail request failed: ${response.status}`);
  }

  return response.json();
}
