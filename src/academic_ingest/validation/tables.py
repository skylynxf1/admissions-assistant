from __future__ import annotations

from academic_ingest.models.domain import EvidenceRecord
from academic_ingest.models.enums import Severity
from academic_ingest.validation.models import ValidationIssue


def validate_table_evidence(evidence: EvidenceRecord) -> list[ValidationIssue]:
    if evidence.table_identifier is None:
        return []
    missing = [
        name
        for name, value in (
            ("heading_context", evidence.heading_context),
            ("row_identifier", evidence.row_identifier),
        )
        if not value
    ]
    if not missing:
        return []
    return [
        ValidationIssue(
            code="incomplete_table_context",
            message="Table evidence is missing: " + ", ".join(missing),
            severity=Severity.WARNING,
            disposition="review",
            evidence_id=evidence.id,
        )
    ]
