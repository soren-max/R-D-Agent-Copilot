export type ProviderConfig = {
  provider: string;
  model: string;
  api_base_url: string;
  timeout: number;
  streaming_enabled: boolean;
  fallback_enabled: boolean;
  api_key_masked: string;
};

export type ModelOption = {
  name: string;
  provider: string;
  context_window: number;
  capabilities: string[];
  status: "available" | "unavailable" | "selected";
};

export type ThemeMode = "light" | "dark" | "system";

export type EnvironmentInfo = {
  frontend_url: string;
  backend_api_base_url: string;
  runtime: string;
  build_mode: string;
  mock_data_enabled: boolean;
  health_status: "healthy" | "degraded" | "unreachable";
};

export type SystemServiceStatus = {
  llm_provider: "healthy" | "degraded" | "unreachable";
  rag_service: "healthy" | "degraded" | "unreachable";
  trace_service: "healthy" | "degraded" | "unreachable";
  evaluation_service: "healthy" | "degraded" | "unreachable";
  safety_guard: "healthy" | "degraded" | "unreachable";
};

export type SettingsState = {
  provider: ProviderConfig;
  models: ModelOption[];
  theme: ThemeMode;
  environment: EnvironmentInfo;
  services: SystemServiceStatus;
  config_source: string;
};

export const mockSettings: SettingsState = {
  provider: {
    provider: "DeepSeek",
    model: "deepseek-v4-flash",
    api_base_url: "https://api.deepseek.com",
    timeout: 30,
    streaming_enabled: true,
    fallback_enabled: true,
    api_key_masked: "sk-****5dec2b",
  },
  models: [
    { name: "deepseek-v4-flash", provider: "DeepSeek", context_window: 65536, capabilities: ["fast", "reasoning", "streaming"], status: "selected" },
    { name: "deepseek-v4-pro", provider: "DeepSeek", context_window: 131072, capabilities: ["reasoning", "complex"], status: "available" },
    { name: "gpt-4o", provider: "OpenAI", context_window: 128000, capabilities: ["reasoning", "vision", "tool_use"], status: "available" },
    { name: "mock-agent-model", provider: "Mock", context_window: 4096, capabilities: ["fallback", "fast", "testing"], status: "available" },
  ],
  theme: "light",
  environment: {
    frontend_url: "http://localhost:3000",
    backend_api_base_url: "http://127.0.0.1:8005",
    runtime: "Node.js 18 / Python 3.12",
    build_mode: "development",
    mock_data_enabled: true,
    health_status: "healthy",
  },
  services: {
    llm_provider: "healthy",
    rag_service: "healthy",
    trace_service: "healthy",
    evaluation_service: "healthy",
    safety_guard: "healthy",
  },
  config_source: ".env + local mock",
};
