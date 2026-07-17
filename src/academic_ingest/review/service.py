from __future__ import annotations

from academic_ingest.conflicts.models import record_type_name
from academic_ingest.models.domain import EvidenceBackedRecord, ReviewTask
from academic_ingest.validation.models import ValidationIssue


def review_task_for_issue(
    record: EvidenceBackedRecord,
    issue: ValidationIssue,
) -> ReviewTask:
    return ReviewTask(
        institution_id=record.institution_id,
        record_type=record_type_name(record),
        record_id=record.id,
        reason=issue.code,
        severity=issue.severity,
        unresolved_question=issue.message,
    )
