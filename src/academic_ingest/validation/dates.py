from __future__ import annotations

from datetime import datetime

from academic_ingest.models.domain import EffectivePeriod
from academic_ingest.models.enums import Severity
from academic_ingest.validation.models import ValidationIssue


def periods_overlap(left: EffectivePeriod, right: EffectivePeriod) -> bool:
    left_start = left.effective_from
    left_end = left.effective_to
    right_start = right.effective_from
    right_end = right.effective_to
    if left_end is not None and right_start is not None and left_end < right_start:
        return False
    return not (right_end is not None and left_start is not None and right_end < left_start)


def validate_effective_dates(
    effective_from: datetime | None,
    effective_to: datetime | None,
) -> list[ValidationIssue]:
    if effective_from is not None and effective_to is not None and effective_to < effective_from:
        return [
            ValidationIssue(
                code="invalid_effective_period",
                message="effective_to precedes effective_from",
                severity=Severity.ERROR,
                disposition="block_publish",
                field="effective_to",
            )
        ]
    return []
