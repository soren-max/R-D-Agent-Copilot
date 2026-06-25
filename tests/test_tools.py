from app.tools import config_tool, git_tool, log_tool
from app.tools.config_tool import ConfigTool
from app.tools.git_tool import GitTool
from app.tools.log_tool import LogTool


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


def test_config_tool_compares_dev_and_prod_config_differences():
    result = ConfigTool().run("订单支付 timeout retry 配置差异")

    assert_tool_contract(result, "config_tool", "data/configs/dev.json,data/configs/prod.json")
    assert "payment.timeout" in result["result"]
    assert "order.retry_count" in result["result"]
    assert "feature.enable_new_payment_flow" in result["result"]
    assert result["confidence"] == 0.85


def test_git_tool_reads_commits_json():
    result = GitTool().run("order-service 异常处理 支付流程")

    assert_tool_contract(result, "git_tool", "data/git/commits.json")
    assert "mock-a1b2c3d" in result["result"]
    assert "risk" not in result
    assert "异常处理" in result["result"] or "payment-service timeout" in result["result"]
    assert result["confidence"] == 0.8


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
