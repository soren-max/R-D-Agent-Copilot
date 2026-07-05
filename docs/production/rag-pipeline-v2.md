# RAG Pipeline v2

RAG Pipeline v2 upgrades the local knowledge pipeline from uniform Markdown chunking to troubleshooting-aware layered processing. It remains local, deterministic, and dependency-light.

## Why Uniform Chunking Is Not Enough

R&D troubleshooting evidence is not shaped like one document type. A runbook paragraph, config file, log excerpt, and code stack context all need different chunk sizes and metadata. Uniform chunking can bury the exact error code, split config key/value pairs, or mix unrelated log events into one large passage.

RAG v2 treats document type as a retrieval signal instead of only a storage detail.

## Layered Chunking

Supported `doc_type` values:

- `normal_doc`
- `markdown_doc`
- `config_file`
- `log_file`
- `code_file`

Chunking policy:

- `normal_doc` and `markdown_doc`: larger chunks for conceptual and runbook-style context.
- `config_file`, `log_file`, and `code_file`: smaller chunks to preserve precise evidence.

Each chunk records:

- `chunk_id`
- `doc_type`
- `source`
- `title`
- `line_range`
- `content_hash`

## Cleaning And Dedup

The cleaning stage removes empty lines, obvious garbled text, and repeated template boilerplate. It preserves troubleshooting evidence:

- Log key lines, error codes, timeout messages, exceptions, and stack summaries.
- Config key/value structure.
- Code function names, class names, and nearby error context.

Dedup is based on normalized text hashes. Non-critical duplicated boilerplate can be removed, while error/config/code evidence is kept when the source or line range matters.

## Two-Layer Retrieval

RAG v2 keeps the existing local vector-style recall first, then applies deterministic rule-based rerank. No external vector database or rerank model is required.

Rerank features:

- Query keyword overlap.
- Error code match.
- Service name match.
- Source/title match.
- Document type priority.

Outputs include `rerank_score` and `match_reason`, so trace and tests can explain why a chunk moved up.

## Precision And Recall Metrics

The v2 metrics are intentionally simple and inspectable:

- `recall_at_k`: whether retrieval returned relevant evidence for the query set or current run.
- `precision_at_k`: retrieved evidence count divided by requested `top_k`.
- `source_coverage`: share of retrieved evidence with usable source/title metadata.
- `missing_source_count`: count of evidence items missing source or title.
- `grounded_answer_rate`: share of grounded RAG runs.
- `rerank_applied`: whether rule-based rerank was applied.
- `dedup_count`: number of duplicate chunks filtered during ingestion.

Evaluation v2 aggregates these into the RAG section of the report.

## Why v2 Does Not Use Qdrant Yet

Qdrant is useful once the project needs persistent vector indexes, larger corpora, and operational search debugging. This v2 deliberately stays local because the current goal is to prove ingestion quality, metadata quality, deterministic rerank, and evaluation metrics before adding an external service.

Avoiding Qdrant at this stage keeps demos and CI fast, reproducible, and safe without Docker services or production-like data.

## Future Qdrant Upgrade

A later local-container upgrade can add Qdrant behind the same retriever contract:

1. Start Qdrant with Docker Compose.
2. Add an ingestion job that writes `content`, vector, and metadata payloads.
3. Keep local fallback for CI and offline demos.
4. Compare Qdrant recall/latency against the current local vector store.
5. Preserve `chunk_id`, `doc_type`, `source`, `title`, `line_range`, and `content_hash` as payload fields.

## 30-Second Interview Version

"RAG v2 makes retrieval troubleshooting-aware. Instead of chunking every file the same way, it detects Markdown, config, logs, and code, then uses larger chunks for runbooks and smaller chunks for precise evidence. It cleans and deduplicates locally, reranks with deterministic signals like error code and service name, and reports precision, recall, source coverage, rerank, and dedup metrics in Evaluation v2."

## 1-Minute Interview Version

"The main problem with uniform RAG chunking in R&D troubleshooting is that evidence has different shapes. A config key/value, a log error line, a stack trace, and a runbook section should not be chunked or ranked the same way. RAG Pipeline v2 adds doc type detection, layered chunking, cleaning, hash-based dedup, and a two-layer retrieval flow: local vector recall followed by deterministic rerank using keyword overlap, error-code match, service-name match, source/title match, and doc-type priority. The output keeps source/title/chunk/line metadata for traceability, and Evaluation v2 aggregates precision@k, recall@k, source coverage, grounded answer rate, rerank applied, and dedup count. It intentionally does not add Qdrant yet, because this stage is about proving data quality and evaluation before adding infrastructure."
