from app.agent.router import IntentRouter


def test_router_classifies_demo_order_500_case_as_troubleshooting():
    result = IntentRouter().route("为什么订单接口报500？配置改了但没有生效，应该怎么排查？")

    assert result.type == "complex_troubleshooting"


def test_router_keeps_config_center_definition_as_simple_qa():
    result = IntentRouter().route("什么是配置中心？")

    assert result.type == "simple_qa"


def test_router_classifies_config_not_effective_as_troubleshooting():
    result = IntentRouter().route("配置改了为什么没有生效？")

    assert result.type == "complex_troubleshooting"


def test_router_classifies_order_500_log_query_as_troubleshooting():
    result = IntentRouter().route("订单接口返回500，应该看哪些日志？")

    assert result.type == "complex_troubleshooting"


def test_router_keeps_langgraph_definition_as_simple_qa():
    result = IntentRouter().route("什么是 LangGraph？")

    assert result.type == "simple_qa"


def test_router_classifies_ci_failure_as_troubleshooting():
    result = IntentRouter().route("GitHub Actions 构建失败应该怎么排查？")

    assert result.type == "complex_troubleshooting"
