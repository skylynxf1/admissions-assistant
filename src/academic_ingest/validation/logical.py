from __future__ import annotations

import re
from decimal import Decimal

from academic_ingest.models.domain import EvidenceBackedRecord, ExamCreditRule, TransferPolicy
from academic_ingest.models.enums import MappingOutcome, Severity
from academic_ingest.validation.models import ValidationIssue

_NO_CREDIT_LANGUAGE = re.compile(
    r"\b(?:no\s+credit(?:\s+is)?\s+(?:awarded|granted)|does\s+not\s+earn\s+credit|zero\s+credit)\b",
    re.IGNORECASE,
)


def validate_exam_awards(
    awarded_courses: list[str],
    awarded_credit_values: list[Decimal | None],
) -> list[ValidationIssue]:
    if awarded_credit_values and len(awarded_courses) != len(awarded_credit_values):
        return [
            ValidationIssue(
                code="exam_award_cardinality_mismatch",
                message="Awarded courses and credit values must have matching cardinality.",
                severity=Severity.ERROR,
                disposition="block_publish",
                field="awarded_credit_values",
            )
        ]
    return []


def validate_mapping_outcome(
    outcome: MappingOutcome,
    source_text: str,
) -> list[ValidationIssue]:
    if outcome == MappingOutcome.EXPLICIT_NO_CREDIT and not _NO_CREDIT_LANGUAGE.search(source_text):
        return [
            ValidationIssue(
                code="unsupported_explicit_no_credit",
                message=(
                    "Explicit no-credit outcomes require affirmative no-credit source language."
                ),
                severity=Severity.ERROR,
                disposition="block_publish",
                field="mapping_outcome",
            )
        ]
    return []


def validate_record_logic(record: EvidenceBackedRecord) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if isinstance(record, ExamCreditRule):
        issues.extend(validate_exam_awards(record.awarded_courses, record.awarded_credit_values))
    if (
        isinstance(record, TransferPolicy)
        and record.credit_limit is not None
        and record.credit_limit < 0
    ):
        issues.append(
            ValidationIssue(
                code="negative_credit_limit",
                message="Transfer credit limits cannot be negative.",
                severity=Severity.ERROR,
                disposition="block_publish",
                field="credit_limit",
            )
        )
    return issues
