from pathlib import Path

import app.agent.synthesizer as synthesizer_module
from app.api.chat import chat_endpoint
from app.core.models import ChatRequest


def _set_llm_disabled(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "false")
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-v4-flash")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")


def _stage(data: dict, name: str) -> dict:
    for step in data["trace"]["steps"]:
        if step["stage"] == name:
            return step
    return {}


def _has_chinese(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def test_day7_simple_qa_end_to_end_with_skipped_nodes(monkeypatch):
    _set_llm_disabled(monkeypatch)

    data = chat_endpoint(ChatRequest(query="什么是配置中心？")).model_dump()

    assert data["route"]["type"] == "simple_qa"
    assert data["plan"]["steps"][0]["action"] == "retrieve_knowledge"
    assert data["plan"]["steps"][0]["tool"] == "rag_retriever"
    assert [result["tool_name"] for result in data["tool_results"]] == ["rag_retriever"]
    assert data["tool_results"][0]["documents"]
    assert _has_chinese(data["answer"])
    assert data["answer_source"] == "fallback"
    assert data["llm_used"] is False
    assert data["evaluation"] is not None
    assert [step["stage"] for step in data["trace"]["steps"]] == [
        "safety",
        "router",
        "planner",
        "executor",
        "synthesizer",
        "grounding_checker",
        "evaluation",
        "evidence",
    ]

    executor_step = _stage(data, "executor")
    assert executor_step["engine"] == "langgraph"
    assert [node["tool_name"] for node in executor_step["skipped_nodes"]] == [
        "log_tool",
        "config_tool",
        "git_tool",
    ]


def test_day7_complex_troubleshooting_end_to_end(monkeypatch):
    _set_llm_disabled(monkeypatch)

    data = chat_endpoint(ChatRequest(query="为什么订单接口报500？")).model_dump()

    assert data["route"]["type"] == "complex_troubleshooting"
    assert [step["tool"] for step in data["plan"]["steps"]] == [
        "log_tool",
        "config_tool",
        "git_tool",
        "rag_retriever",
    ]
    assert [result["tool_name"] for result in data["tool_results"]] == [
        "log_tool",
        "config_tool",
        "git_tool",
        "rag_retriever",
    ]
    assert all(result["status"] == "success" for result in data["tool_results"])
    assert data["tool_results"][-1]["documents"]

    executor_step = _stage(data, "executor")
    assert executor_step["engine"] == "langgraph"
    assert all(
        set(["node", "tool_name", "status", "latency_ms"]).issubset(call)
        for call in executor_step["tool_calls"]
    )

    for required_text in ["初步判断", "工具证据", "知识库补充", "建议处理方式"]:
        assert required_text in data["answer"]


def test_day7_llm_disabled_fallback(monkeypatch):
    _set_llm_disabled(monkeypatch)

    data = chat_endpoint(ChatRequest(query="为什么订单接口报500？")).model_dump()

    assert data["answer_source"] == "fallback"
    assert data["llm_used"] is False
    assert data["llm_error"] == "llm_disabled"
    assert _stage(data, "synthesizer")["engine"] == "fallback"


def test_day7_missing_api_key_fallback(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-v4-flash")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")

    data = chat_endpoint(ChatRequest(query="为什么订单接口报500？")).model_dump()

    assert data["answer_source"] == "fallback"
    assert data["llm_used"] is False
    assert data["llm_error"] == "missing_api_key"
    assert _stage(data, "synthesizer")["engine"] == "fallback"


def test_day7_monkeypatched_llm_success_generates_chinese_answer(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-v4-flash")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-api-key")

    def fake_generate(self, system_prompt, user_prompt):
        return "1. 初步判断\n这是模拟的中文回答。"

    monkeypatch.setattr(synthesizer_module.LLMClient, "generate", fake_generate)

    data = chat_endpoint(ChatRequest(query="为什么订单接口报500？")).model_dump()

    assert data["answer_source"] == "llm"
    assert data["llm_used"] is True
    assert data["llm_error"] is None
    assert _has_chinese(data["answer"])
    assert _stage(data, "synthesizer")["engine"] == "deepseek"
    assert _stage(data, "synthesizer")["prompt_version"] == "synthesizer_prompt_v1"


def test_day7_env_files_do_not_commit_real_api_key():
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    env_example = Path(".env.example").read_text(encoding="utf-8")

    assert ".env" in {
        line.strip()
        for line in gitignore.splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    assert "DEEPSEEK_API_KEY=" in env_example
    assert "sk-" not in env_example
