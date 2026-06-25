export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export const CHAT_ENDPOINT = `${API_BASE_URL}/chat`;

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
};

export type ChatResponse = {
  answer: string;
  answer_source: "fallback" | "llm" | string;
  llm_used: boolean;
  llm_error?: string | null;
  route: RouteResult;
  plan: PlanResult;
  tool_results: ToolResult[];
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
