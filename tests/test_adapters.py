from app.adapters import (
    AdapterResult,
    LocalConfigAdapter,
    LocalGitAdapter,
    LocalLogAdapter,
)


def assert_adapter_result_contract(result: AdapterResult, adapter_name: str, source: str) -> None:
    assert result.adapter_name == adapter_name
    assert result.status in {"success", "failed"}
    assert result.source == source
    assert 0.0 <= result.confidence <= 1.0
    assert result.latency_ms >= 0


def test_adapter_result_can_be_created():
    result = AdapterResult(
        adapter_name="test_adapter",
        status="success",
        data={"ok": True},
        source="local_mock",
        confidence=0.5,
        error=None,
        latency_ms=1.2,
    )

    assert_adapter_result_contract(result, "test_adapter", "local_mock")
    assert result.data == {"ok": True}
    assert result.error is None


def test_local_log_adapter_search_logs_returns_adapter_result():
    result = LocalLogAdapter().search_logs("订单接口 500", context="order-service")

    assert isinstance(result, AdapterResult)
    assert_adapter_result_contract(
        result,
        "mock_api_log_adapter",
        "mock_api:/mock/logs",
    )
    assert "order-service" in result.data
    assert "status=500" in result.data
    assert result.confidence == 0.9


def test_local_config_adapter_compare_configs_returns_adapter_result():
    result = LocalConfigAdapter().compare_configs("支付超时配置", context="dev vs prod")

    assert isinstance(result, AdapterResult)
    assert_adapter_result_contract(
        result,
        "mock_api_config_adapter",
        "mock_api:/mock/configs",
    )
    assert "payment.timeout" in result.data
    assert "feature.enable_new_payment_flow" in result.data
    assert result.confidence == 0.85


def test_local_git_adapter_search_commits_returns_adapter_result():
    result = LocalGitAdapter().search_commits("payment timeout", context="order-service")

    assert isinstance(result, AdapterResult)
    assert_adapter_result_contract(
        result,
        "mock_api_git_adapter",
        "mock_api:/mock/git/commits",
    )
    assert "mock-a1b2c3d" in result.data
    assert "payment-service timeout" in result.data
    assert result.confidence == 0.8


def test_local_adapters_do_not_call_external_apis(monkeypatch):
    def fail_network_call(*args, **kwargs):
        raise AssertionError("external API call is not allowed")

    monkeypatch.setattr("socket.socket", fail_network_call)

    log_result = LocalLogAdapter().search_logs("订单接口 500")
    config_result = LocalConfigAdapter().compare_configs("配置差异")
    git_result = LocalGitAdapter().search_commits("最近提交")

    assert log_result.status == "success"
    assert config_result.status == "success"
    assert git_result.status == "success"
