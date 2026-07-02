"""Rule-based claim extraction from Chinese troubleshooting reports."""

from __future__ import annotations

import re

from apps.api.app.rag.schemas import ExtractedClaim


_SECTION_PATTERN = re.compile(r"【([^】]+)】")


class ClaimExtractor:
    """Extract short factual claims from report sections."""

    def extract(self, answer: str) -> list[ExtractedClaim]:
        claims: list[ExtractedClaim] = []
        active_section = ""
        claim_index = 1
        for raw_line in answer.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            match = _SECTION_PATTERN.match(line)
            if match:
                active_section = match.group(1).strip()
                line = _SECTION_PATTERN.sub("", line, count=1).strip()
            for sentence in _split_sentences(line):
                if not _is_checkable(sentence):
                    continue
                claims.append(
                    ExtractedClaim(
                        claim_id=f"claim_{claim_index:03d}",
                        text=sentence,
                        section=active_section,
                    )
                )
                claim_index += 1
        return claims


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"[。！？；;\n]", text)
    return [part.strip(" ：:") for part in parts if part.strip(" ：:")]


def _is_checkable(sentence: str) -> bool:
    if len(sentence) < 8:
        return False
    skip_prefixes = ("建议", "继续", "优先", "核对", "回查", "以上结论", "风险提示")
    return not sentence.startswith(skip_prefixes)
