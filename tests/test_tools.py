from app.tools import config_tool, git_tool, log_tool
from app.tools.config_tool import ConfigTool
from app.tools.git_tool import GitTool
from app.tools.log_tool import LogTool
from app.adapters.base import AdapterResult


def assert_tool_contract(result, tool_name, source):
    assert result["tool_name"] == tool_name
    assert "result" in result
    assert "confidence" in result
    assert 0 <= result["confidence"] <= 1
    assert result["source"] == source


def test_log_tool_reads_order_service_log():
    result = LogTool().run("为什么订单接口报500？")

    assert_tool_contract(result, "log_tool", "data/logs/order-service.log")
    assert "order-service" in result["result"]
    assert "status=500" in result["result"]
    assert "mock-trace-001" in result["result"]
    assert result["confidence"] == 0.9


def test_log_tool_uses_local_log_adapter(monkeypatch):
    calls = {"count": 0}

    def fake_search_logs(self, query, context=""):
        calls["count"] += 1
        assert query == "订单接口报500"
        return AdapterResult(
            adapter_name="local_log_adapter",
            status="success",
            data="adapter log summary",
            source="data/logs/order-service.log",
            confidence=0.9,
        )

    monkeypatch.setattr(log_tool.LocalLogAdapter, "search_logs", fake_search_logs)

    result = LogTool().run("订单接口报500")

    assert calls["count"] == 1
    assert_tool_contract(result, "log_tool", "data/logs/order-service.log")
    assert result["result"] == "adapter log summary"


def test_config_tool_compares_dev_and_prod_config_differences():
    result = ConfigTool().run("订单支付 timeout retry 配置差异")

    assert_tool_contract(result, "config_tool", "data/configs/dev.json,data/configs/prod.json")
    assert "payment.timeout" in result["result"]
    assert "order.retry_count" in result["result"]
    assert "feature.enable_new_payment_flow" in result["result"]
    assert result["confidence"] == 0.85


def test_config_tool_uses_local_config_adapter(monkeypatch):
    calls = {"count": 0}

    def fake_compare_configs(self, query, context=""):
        calls["count"] += 1
        assert query == "配置差异"
        return AdapterResult(
            adapter_name="local_config_adapter",
            status="success",
            data="adapter config diff",
            source="data/configs/dev.json,data/configs/prod.json",
            confidence=0.85,
        )

    monkeypatch.setattr(config_tool.LocalConfigAdapter, "compare_configs", fake_compare_configs)

    result = ConfigTool().run("配置差异")

    assert calls["count"] == 1
    assert_tool_contract(result, "config_tool", "data/configs/dev.json,data/configs/prod.json")
    assert result["result"] == "adapter config diff"


def test_git_tool_reads_commits_json():
    result = GitTool().run("order-service 异常处理 支付流程")

    assert_tool_contract(result, "git_tool", "data/git/commits.json")
    assert "mock-a1b2c3d" in result["result"]
    assert "risk" not in result
    assert "异常处理" in result["result"] or "payment-service timeout" in result["result"]
    assert result["confidence"] == 0.8


def test_git_tool_uses_local_git_adapter(monkeypatch):
    calls = {"count": 0}

    def fake_search_commits(self, query, context=""):
        calls["count"] += 1
        assert query == "提交摘要"
        return AdapterResult(
            adapter_name="local_git_adapter",
            status="success",
            data="adapter commit summary",
            source="data/git/commits.json",
            confidence=0.8,
        )

    monkeypatch.setattr(git_tool.LocalGitAdapter, "search_commits", fake_search_commits)

    result = GitTool().run("提交摘要")

    assert calls["count"] == 1
    assert_tool_contract(result, "git_tool", "data/git/commits.json")
    assert result["result"] == "adapter commit summary"


def test_tools_return_structured_error_when_file_missing(monkeypatch, tmp_path):
    missing = tmp_path / "missing.fixture"

    monkeypatch.setattr(log_tool, "LOG_FILE", missing)
    log_result = LogTool().run("订单报错")
    assert_tool_contract(log_result, "log_tool", "data/logs/order-service.log")
    assert log_result["result"] == ""
    assert log_result["confidence"] == 0.0
    assert log_result["error"] == "file_not_found"

    monkeypatch.setattr(config_tool, "DEV_CONFIG_FILE", missing)
    config_result = ConfigTool().run("订单配置")
    assert_tool_contract(config_result, "config_tool", "data/configs/dev.json,data/configs/prod.json")
    assert config_result["result"] == ""
    assert config_result["confidence"] == 0.0
    assert config_result["error"] == "file_not_found"

    monkeypatch.setattr(git_tool, "GIT_FILE", missing)
    git_result = GitTool().run("订单异常")
    assert_tool_contract(git_result, "git_tool", "data/git/commits.json")
    assert git_result["result"] == ""
    assert git_result["confidence"] == 0.0
    assert git_result["error"] == "file_not_found"
