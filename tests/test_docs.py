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
