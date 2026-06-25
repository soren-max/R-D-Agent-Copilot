from pathlib import Path


def test_local_knowledge_base_docs_exist_and_are_non_empty():
    docs_dir = Path("data/docs")

    assert docs_dir.exists()
    markdown_files = sorted(docs_dir.glob("*.md"))
    assert len(markdown_files) >= 4

    for path in markdown_files:
        assert path.read_text(encoding="utf-8").strip()
