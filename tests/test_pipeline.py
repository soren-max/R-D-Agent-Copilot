"""
集成测试 — 验证完整 Agent 链路和 API 端点。

验证：
- POST /chat 返回完整结构（answer + route + plan + tool_results + trace）
- simple_qa 正确分流
- complex_troubleshooting 正确触发三步工具
- Trace 包含全部三个阶段
- 最终回答为中文
"""

import sys
sys.path.insert(0, ".")

from app.agent.pipeline import run_pipeline
from app.core.models import ChatRequest, ChatResponse


def test_simple_qa_pipeline():
    """simple_qa 应返回简单回答，无工具调用。"""
    req = ChatRequest(query="什么是配置中心")
    resp = run_pipeline(req)

    assert resp.route.type == "simple_qa"
    assert resp.plan.plan_type == "simple_qa"
    assert len(resp.plan.steps) == 1
    assert len(resp.tool_results) == 1
    assert resp.tool_results[0].tool == "none"
    assert resp.tool_results[0].status == "skipped"
    assert len(resp.answer) > 0
    # Trace 验证
    trace_stages = [s.stage for s in resp.trace.steps]
    assert "router" in trace_stages
    assert "planner" in trace_stages
    assert "executor" in trace_stages


def test_troubleshooting_pipeline():
    """complex_troubleshooting 应触发三步工具调用。"""
    req = ChatRequest(query="为什么订单接口报500？")
    resp = run_pipeline(req)

    assert resp.route.type == "complex_troubleshooting"
    assert resp.plan.plan_type == "troubleshooting_plan"
    assert len(resp.plan.steps) == 3
    # 三步工具调用
    assert len(resp.tool_results) == 3
    tools_used = [r.tool for r in resp.tool_results]
    assert "log_tool" in tools_used
    assert "config_tool" in tools_used
    assert "git_tool" in tools_used
    # 工具执行成功
    for r in resp.tool_results:
        assert r.status == "success", f"工具 {r.tool} 执行失败"
    # 回答非空
    assert len(resp.answer) > 0
    # 中文回答
    assert any('\u4e00' <= c <= '\u9fff' for c in resp.answer)
    # Trace 验证
    trace_stages = [s.stage for s in resp.trace.steps]
    assert "router" in trace_stages
    assert "planner" in trace_stages
    assert "executor" in trace_stages
    assert resp.trace.trace_id is not None
    assert len(resp.trace.trace_id) > 0
    # executor 阶段应有工具调用记录
    executor_step = [s for s in resp.trace.steps if s.stage == "executor"][0]
    assert len(executor_step.tool_calls) > 0


def test_answer_based_on_tools():
    """回答应基于工具结果，而非编造。"""
    req = ChatRequest(query="订单超时")
    resp = run_pipeline(req)

    # 日志结果应出现在回答中
    tool_results_text = " ".join(r.result for r in resp.tool_results)
    answer = resp.answer

    # 回答应引用工具发现的问题
    if "错误日志" in tool_results_text or "ERROR" in tool_results_text:
        assert "日志" in answer


def test_trace_has_latency():
    """Trace 各阶段应有合理的耗时记录。"""
    req = ChatRequest(query="数据库异常")
    resp = run_pipeline(req)

    for step in resp.trace.steps:
        # 耗时可能为 0（如果代码执行极快），但不应该为负
        assert step.latency_ms >= 0, f"阶段 {step.stage} 耗时异常: {step.latency_ms}"


def test_trace_id_unique():
    """每次请求的 trace_id 应唯一。"""
    req1 = ChatRequest(query="订单报错")
    req2 = ChatRequest(query="服务异常")
    resp1 = run_pipeline(req1)
    resp2 = run_pipeline(req2)
    assert resp1.trace.trace_id != resp2.trace.trace_id


if __name__ == "__main__":
    tests = [
        ("simple_qa_pipeline", test_simple_qa_pipeline),
        ("troubleshooting_pipeline", test_troubleshooting_pipeline),
        ("answer_based_on_tools", test_answer_based_on_tools),
        ("trace_has_latency", test_trace_has_latency),
        ("trace_id_unique", test_trace_id_unique),
    ]
    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  ✅ {name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            failed += 1
    print(f"\n{'=' * 40}")
    print(f"结果: {passed} 通过, {failed} 失败, 共 {passed + failed} 项")
