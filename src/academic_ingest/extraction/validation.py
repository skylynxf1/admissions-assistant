from __future__ import annotations

from academic_ingest.extraction.schemas.policy import ExtractionContext, ExtractionProposal
from academic_ingest.validation.evidence import validate_evidence


def validate_extraction_proposal(
    context: ExtractionContext,
    proposal: ExtractionProposal,
) -> list[str]:
    issues: list[str] = []
    if proposal.proposed_fields and not proposal.exact_evidence_strings:
        issues.append("missing_exact_evidence")
    supplied = context.supplied_source_text().encode("utf-8")
    for quote in proposal.exact_evidence_strings:
        check = validate_evidence(quote, supplied)
        if not check.accepted:
            issues.append(f"evidence_not_found: {quote}")
    for source_url in proposal.source_urls:
        if source_url != context.canonical_url:
            issues.append(f"unsupported_source_url: {source_url}")
    return issues
