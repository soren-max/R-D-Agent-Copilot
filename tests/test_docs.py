from pathlib import Path


def test_local_knowledge_base_docs_exist_and_are_non_empty():
    docs_dir = Path("data/docs")

    assert docs_dir.exists()
    markdown_files = sorted(docs_dir.glob("*.md"))
    assert len(markdown_files) >= 4

    for path in markdown_files:
        assert path.read_text(encoding="utf-8").strip()


def test_day5_langgraph_demo_docs_and_script_exist():
    doc_path = Path("docs/day5-langgraph-demo.md")
    script_path = Path("scripts/demo_day5.py")

    assert doc_path.exists()
    assert script_path.exists()

    doc = doc_path.read_text(encoding="utf-8")
    for required_text in [
        "LangGraph 条件工具执行",
        "工具失败 retry",
        "fallback 策略",
        "User -> Router -> Planner -> Executor -> LangGraph Tool Nodes -> Trace -> Response",
        "Demo Case 1：简单问答",
        "Demo Case 2：复杂排障",
        "Demo Case 3：工具失败 fallback",
        "部分工具查询失败",
    ]:
        assert required_text in doc


def test_day6_env_example_contains_required_llm_config():
    env_example = Path(".env.example").read_text(encoding="utf-8")

    for required_text in [
        "LLM_ENABLED=false",
        "LLM_PROVIDER=deepseek",
        "LLM_MODEL=deepseek-v4-flash",
        "LLM_BASE_URL=https://api.deepseek.com",
        "DEEPSEEK_API_KEY=",
    ]:
        assert required_text in env_example


def test_readme_contains_deepseek_answer_synthesizer_section():
    readme = Path("README.md").read_text(encoding="utf-8")

    for required_text in [
        "## DeepSeek Answer Synthesizer",
        "DeepSeek API 当前只用于最终回答生成",
        "默认关闭",
        "fallback",
        "Router",
        "Planner",
        "Tool Selection",
    ]:
        assert required_text in readme


def test_day6_deepseek_demo_docs_and_script_exist():
    doc_path = Path("docs/day6-deepseek-demo.md")
    script_path = Path("scripts/demo_day6.py")

    assert doc_path.exists()
    assert script_path.exists()

    doc = doc_path.read_text(encoding="utf-8")
    for required_text in [
        "DeepSeek 只用于 Answer Synthesizer",
        "cp .env.example .env",
        "Demo Case 1：LLM 关闭",
        "Demo Case 2：LLM 开启",
        "fallback 策略",
        "answer_source = fallback",
        "synthesizer.engine = deepseek",
        "我没有让大模型直接控制整个 Agent 流程",
    ]:
        assert required_text in doc
