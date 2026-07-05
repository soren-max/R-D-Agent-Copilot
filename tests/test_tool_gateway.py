from app.api.chat import chat_endpoint
from app.core.models import ChatRequest
from app.tools.gateway import ToolGateway
from app.tools.policies import ToolGatewayPolicy
from app.tools.registry import ToolRegistry


class EchoTool:
    name = "echo_tool"

    def run(self, query: str):
        return {
            "tool_name": self.name,
            "result": f"echo:{query}",
            "confidence": 0.7,
            "source": "unit_test",
        }


class PartialTool:
    name = "partial_tool"

    def run(self, query: str):
        return {
            "tool_name": self.name,
            "status": "partial_success",
            "result": "部分数据返回",
            "confidence": 0.4,
            "source": "unit_test",
            "documents": [{"source": "doc.md", "content": "partial"}],
        }


def _registry(tool_name: str, factory):
    registry = ToolRegistry()
    registry.register(tool_name, factory)
    return registry


def _gateway(tool_name: str, factory):
    return ToolGateway(
        registry=_registry(tool_name, factory),
        policy=ToolGatewayPolicy(allowed_tools={tool_name}),
    )


def test_unregistered_tool_is_blocked():
    result = ToolGateway(registry=ToolRegistry()).execute("unknown_tool", {"query": "hello"})

    assert result.status == "blocked"
    assert result.error_code == "tool_not_registered"
    assert result.tool_name == "unknown_tool"


def test_missing_query_returns_error():
    result = _gateway("echo_tool", EchoTool).execute("echo_tool", {})

    assert result.status == "error"
    assert result.error_code == "missing_query"


def test_duplicate_call_is_blocked():
    gateway = _gateway("echo_tool", EchoTool)

    first = gateway.execute("echo_tool", {"query": "same"})
    second = gateway.execute("echo_tool", {"query": "same"})

    assert first.status == "success"
    assert second.status == "blocked"
    assert second.error_code == "duplicate_call"
    assert second.input_hash == first.input_hash


def test_successful_tool_returns_standard_result():
    result = _gateway("echo_tool", EchoTool).execute("echo_tool", {"query": "hello"})

    assert result.tool_name == "echo_tool"
    assert result.status == "success"
    assert result.latency_ms >= 0
    assert result.input_hash
    assert result.evidence_count == 1
    assert result.safe_summary == "echo:hello"
    assert result.metadata["raw_output"]["source"] == "unit_test"


def test_partial_success_is_recorded():
    result = _gateway("partial_tool", PartialTool).execute(
        "partial_tool",
        {"query": "partial"},
    )

    assert result.status == "partial_success"
    assert result.evidence_count == 1
    assert result.error_code == ""


def test_trace_contains_tool_gateway_metadata(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-v4-flash")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")
    monkeypatch.setenv("LLM_ENABLED", "false")

    data = chat_endpoint(ChatRequest(query="什么是配置中心？")).model_dump()
    executor_step = [step for step in data["trace"]["steps"] if step["stage"] == "executor"][0]
    tool_call = executor_step["tool_calls"][0]

    assert tool_call["tool_status"] == "success"
    assert tool_call["latency_ms"] >= 0
    assert tool_call["error_code"] == ""
    assert tool_call["input_hash"]
