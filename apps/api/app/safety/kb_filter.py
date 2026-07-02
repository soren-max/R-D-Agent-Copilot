"""Filter malicious instructions from local KB documents."""

from __future__ import annotations

from apps.api.app.rag.loader import MarkdownDocument
from apps.api.app.safety.prompt_injection import detect_prompt_injection
from apps.api.app.safety.schemas import KbFilterResult


def filter_malicious_documents(
    documents: list[MarkdownDocument],
) -> tuple[list[MarkdownDocument], list[KbFilterResult]]:
    allowed: list[MarkdownDocument] = []
    results: list[KbFilterResult] = []
    for document in documents:
        safety = detect_prompt_injection(document.content)
        if safety.blocked:
            results.append(
                KbFilterResult(
                    source=document.source,
                    allowed=False,
                    reason=";".join(safety.reasons),
                )
            )
            continue
        results.append(KbFilterResult(source=document.source, allowed=True))
        allowed.append(document)
    return allowed, results
