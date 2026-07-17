from __future__ import annotations

import re
from collections.abc import Mapping
from uuid import UUID

from pydantic import BaseModel
from selectolax.parser import HTMLParser

from academic_ingest.models.domain import EvidenceBackedRecord
from academic_ingest.models.enums import Severity
from academic_ingest.validation.dates import validate_effective_dates
from academic_ingest.validation.logical import validate_record_logic
from academic_ingest.validation.models import ValidationIssue, ValidationReport
from academic_ingest.validation.source_scope import validate_source_scope
from academic_ingest.validation.tables import validate_table_evidence


class EvidenceValidation(BaseModel):
    accepted: bool
    code: str
    message: str


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _visible_snapshot_text(snapshot: bytes) -> str:
    decoded = snapshot.decode("utf-8", errors="replace")
    if "<" not in decoded or ">" not in decoded:
        return _normalize_text(decoded)
    tree = HTMLParser(decoded)
    if tree.root is None:
        return _normalize_text(decoded)
    return _normalize_text(tree.root.text(separator=" ", strip=True))


def validate_evidence(evidence_text: str, snapshot: bytes) -> EvidenceValidation:
    quote = _normalize_text(evidence_text)
    visible_text = _visible_snapshot_text(snapshot)
    if quote and quote in visible_text:
        return EvidenceValidation(
            accepted=True,
            code="exact_evidence_verified",
            message="Evidence quote was verified in normalized visible snapshot text.",
        )
    return EvidenceValidation(
        accepted=False,
        code="evidence_not_found",
        message="Evidence quote does not occur in the source snapshot.",
    )


def validate_candidate(
    candidate: EvidenceBackedRecord,
    snapshot: bytes | Mapping[UUID, bytes],
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    if not candidate.evidence:
        issues.append(
            ValidationIssue(
                code="missing_exact_evidence",
                message="At least one exact evidence quote is required for publication.",
                severity=Severity.ERROR,
                disposition="block_publish",
            )
        )
    for evidence in candidate.evidence:
        raw_snapshot: bytes | None
        if isinstance(snapshot, bytes):
            raw_snapshot = snapshot
        else:
            raw_snapshot = snapshot.get(evidence.source_snapshot_id)
            if raw_snapshot is None:
                issues.append(
                    ValidationIssue(
                        code="snapshot_not_available",
                        message="The evidence source snapshot was not supplied to the validator.",
                        severity=Severity.ERROR,
                        disposition="block_publish",
                        evidence_id=evidence.id,
                    )
                )
                continue
        check = validate_evidence(evidence.evidence_text, raw_snapshot)
        if not check.accepted:
            issues.append(
                ValidationIssue(
                    code=check.code,
                    message=check.message,
                    severity=Severity.ERROR,
                    disposition="block_publish",
                    evidence_id=evidence.id,
                )
            )
        issues.extend(validate_source_scope(evidence.source_url, candidate.campus))
        issues.extend(validate_table_evidence(evidence))
    issues.extend(validate_effective_dates(candidate.effective_from, candidate.effective_to))
    issues.extend(validate_record_logic(candidate))
    return ValidationReport(
        accepted=not any(issue.disposition == "block_publish" for issue in issues),
        issues=issues,
    )
