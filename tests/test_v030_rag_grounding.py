from app.agent.synthesizer import Synthesizer
from app.api.chat import chat_endpoint
from app.core.models import Plan, RouterResult
from app.core.models import ChatRequest
from apps.api.app.rag import (
    GroundingChecker,
    KeywordRetriever,
    LocalReranker,
    VectorSearchIndex,
    build_evidence,
    chunk_documents,
    load_markdown_documents,
    rewrite_query,
)
from apps.api.app.rag.claim_extractor import ClaimExtractor
from apps.api.app.rag.evaluation import RagEvalCase, evaluate_cases, load_eval_cases
from apps.api.app.rag.keyword_search import KeywordSearchIndex
from pathlib import Path


def test_v030_loader_loads_markdown_kb_documents():
    documents = load_markdown_documents()

    assert len(documents) >= 6
    assert {document.source.rsplit("/", 1)[-1] for document in documents} >= {
        "deployment_guide.md",
        "redis_common_issues.md",
        "nginx_error_guide.md",
        "database_slow_query.md",
        "ci_cd_failure_cases.md",
        "git_rollback_playbook.md",
    }
    assert all(document.title for document in documents)
    assert all(document.content for document in documents)


def test_v030_chunker_produces_required_chunk_shape():
    chunks = chunk_documents(load_markdown_documents())

    assert chunks
    first = chunks[0]
    assert first.chunk_id
    assert first.source.startswith("apps/api/app/kb/")
    assert first.title
    assert first.content
    assert first.keywords


def test_v030_keyword_search_supports_chinese_and_english_keywords():
    chunks = chunk_documents(load_markdown_documents())
    hits = KeywordSearchIndex(chunks).search("Redis timeout 连接池", top_k=3)

    assert hits
    assert hits[0].score > 0
    assert any("redis_common_issues.md" in hit.chunk.source for hit in hits)


def test_v030_evidence_builder_converts_chunks_to_evidence():
    hits = KeywordSearchIndex(chunk_documents(load_markdown_documents())).search("nginx 502 upstream", top_k=2)
    evidence = build_evidence(hits)

    assert evidence
    first = evidence[0]
    assert first.source
    assert first.chunk_id
    assert first.content_excerpt
    assert 0 < first.score <= 1


def test_v030_empty_evidence_answer_does_not_invent():
    answer = Synthesizer().synthesize(
        "线上服务是不是因为某条不存在的命令失败？",
        RouterResult(type="complex_troubleshooting", intent="log_analysis", confidence=0.9, reason="test"),
        Plan(plan_type="troubleshooting_plan", task_type="log_analysis", steps=[]),
        [],
    )

    assert "当前证据不足" in answer
    assert "不存在的命令失败" not in answer


def test_v030_port_already_in_use_retrieves_deployment_guide():
    chunks = KeywordRetriever().retrieve("port already in use 服务启动失败", top_k=3)

    assert chunks
    assert chunks[0]["source"] == "apps/api/app/kb/deployment_guide.md"
    assert "port already in use" in chunks[0]["content"].lower()


def test_v030_trace_records_rag_grounding_fields(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "false")

    data = chat_endpoint(ChatRequest(query="port already in use 服务启动失败")).model_dump()
    executor_step = [step for step in data["trace"]["steps"] if step["stage"] == "executor"][0]

    assert executor_step["query"] == "port already in use 服务启动失败"
    assert executor_step["retrieved_chunks"]
    assert executor_step["evidence"]
    assert executor_step["grounding_status"] == "grounded"
    assert executor_step["no_evidence_reason"] == ""


def test_v031_query_rewrite_expands_chinese_port_conflict():
    rewrite = rewrite_query("服务启动失败，端口被占用")

    assert "port already in use" in rewrite.expansions
    assert len(rewrite.all_queries()) >= 2


def test_v031_query_rewrite_improves_chinese_port_retrieval():
    chunks = KeywordRetriever().retrieve("服务启动失败，端口被占用", top_k=3)

    assert chunks
    assert chunks[0]["source"] == "apps/api/app/kb/deployment_guide.md"


def test_v031_rag_evaluation_reports_recall_and_mrr():
    metrics = evaluate_cases([
        RagEvalCase(
            query="服务启动失败，端口被占用",
            expected_sources=["apps/api/app/kb/deployment_guide.md"],
            expected_keywords=["port already in use"],
        ),
        RagEvalCase(
            query="nginx 返回 502",
            expected_sources=["apps/api/app/kb/nginx_error_guide.md"],
            expected_keywords=["502"],
        ),
    ])

    assert metrics["Recall@5"] == 1.0
    assert metrics["MRR"] == 1.0
    assert metrics["failed_cases"] == []


def test_v031_trace_records_query_rewrite_fields(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "false")

    data = chat_endpoint(ChatRequest(query="服务启动失败，端口被占用")).model_dump()
    executor_step = [step for step in data["trace"]["steps"] if step["stage"] == "executor"][0]

    assert "port already in use" in executor_step["query_expansions"]
    assert len(executor_step["rewritten_queries"]) >= 2


def test_v032_vector_search_returns_semantic_hits():
    chunks = chunk_documents(load_markdown_documents())
    hits = VectorSearchIndex(chunks).search("upstream proxy timeout", top_k=3)

    assert hits
    assert any("nginx_error_guide.md" in hit.chunk.source for hit in hits)
    assert all(hit.retrieval_type == "vector" for hit in hits)


def test_v032_hybrid_search_merges_keyword_and_vector_hits():
    result = KeywordRetriever().retrieve_with_evidence("nginx 502 upstream", top_k=5, retrieval_type="hybrid")

    assert result["retrieval_type"] == "hybrid"
    assert result["retrieved_chunks"]
    assert result["keyword_hit_count"] >= 1
    assert result["vector_hit_count"] >= 1
    assert {chunk["chunk_id"] for chunk in result["retrieved_chunks"]}


def test_v032_rag_eval_loads_20_cases_and_reports_grounding_metrics():
    cases = load_eval_cases(Path("eval/rag_v030_eval_cases.jsonl"))
    metrics = evaluate_cases(cases, top_k=5, retrieval_type="hybrid", baseline_retrieval_type="keyword")

    assert len(cases) == 20
    assert 0 <= metrics["Recall@5"] <= 1
    assert 0 <= metrics["Grounding Score"] <= 1
    assert metrics["No Evidence Rejection Accuracy"] == 1.0
    assert "baseline" in metrics
    assert "improvement" in metrics


def test_v040_reranker_outputs_sorted_rerank_results():
    retriever = KeywordRetriever()
    hits = retriever.search("服务启动失败 port already in use", top_k=5, retrieval_type="hybrid")
    reranked_hits, rerank_results = LocalReranker().rerank("服务启动失败 port already in use", hits, top_k=3)

    assert len(reranked_hits) <= 3
    assert rerank_results
    assert rerank_results[0].final_score >= rerank_results[-1].final_score
    assert rerank_results[0].chunk_id


def test_v040_claim_extractor_extracts_checkable_claims():
    answer = "【初步判断】服务启动失败可能与 port already in use 有关。\n【风险提示】以上结论只基于证据。"
    claims = ClaimExtractor().extract(answer)

    assert claims
    assert claims[0].text == "服务启动失败可能与 port already in use 有关"


def test_v040_grounding_checker_reports_unsupported_claims():
    answer = "【初步判断】服务启动失败可能与 port already in use 有关。数据库主库已经损坏。"
    evidence = [{
        "source": "apps/api/app/kb/deployment_guide.md",
        "chunk_id": "deployment_guide.md#chunk-1",
        "content_excerpt": "service fails to start with port already in use",
        "score": 0.9,
    }]

    result = GroundingChecker().check(answer, evidence)

    assert result.grounded_claims
    assert result.unsupported_claims
    assert result.unsupported_claims[0].text == "数据库主库已经损坏"


def test_v040_chat_response_includes_grounding_check(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "false")

    data = chat_endpoint(ChatRequest(query="服务启动失败，端口被占用")).model_dump()
    grounding_step = [step for step in data["trace"]["steps"] if step["stage"] == "grounding_checker"][0]

    assert data["grounding_check"] is not None
    assert "unsupported_claims" in data
    assert "grounded_claims" in data
    assert 0 <= data["grounding_check"]["grounding_score"] <= 1
    assert grounding_step["claim_grounding_score"] == data["grounding_check"]["grounding_score"]
