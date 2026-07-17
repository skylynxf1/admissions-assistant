from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import Any

from academic_ingest.conflicts.models import canonical_record_key, record_type_name
from academic_ingest.models.domain import ConflictRecord, EffectivePeriod, EvidenceBackedRecord
from academic_ingest.validation.dates import periods_overlap

_NON_CLAIM_FIELDS = {
    "id",
    "institution_id",
    "campus",
    "evidence",
    "warnings",
    "unresolved_fields",
    "parser_name",
    "parser_version",
    "crawl_job_id",
    "authority_tier",
    "confidence_tier",
    "review_status",
    "effective_from",
    "effective_to",
}


def _claim(record: EvidenceBackedRecord) -> dict[str, Any]:
    return {
        key: value
        for key, value in record.model_dump(mode="python").items()
        if key not in _NON_CLAIM_FIELDS
    }


def _different_fields(records: Sequence[EvidenceBackedRecord]) -> dict[str, list[Any]]:
    claims = [_claim(record) for record in records]
    differences: dict[str, list[Any]] = {}
    for field in sorted(set().union(*(claim.keys() for claim in claims))):
        values: list[Any] = []
        for claim in claims:
            value = claim.get(field)
            if value not in values:
                values.append(value)
        if len(values) > 1:
            differences[field] = values
    return differences


def detect_conflicts(records: Sequence[EvidenceBackedRecord]) -> list[ConflictRecord]:
    groups: dict[tuple[str, str], list[EvidenceBackedRecord]] = defaultdict(list)
    for record in records:
        groups[(record_type_name(record), canonical_record_key(record))].append(record)

    conflicts: list[ConflictRecord] = []
    for (record_type, _), group in groups.items():
        overlapping = [
            record
            for record in group
            if any(other.id != record.id and periods_overlap(record, other) for other in group)
        ]
        if len(overlapping) < 2:
            continue
        differing_fields = _different_fields(overlapping)
        if not differing_fields:
            continue
        conflicts.append(
            ConflictRecord(
                institution_id=overlapping[0].institution_id,
                record_type=record_type,
                record_ids=[record.id for record in overlapping],
                conflict_type="overlapping_claims",
                differing_fields=differing_fields,
                source_authorities=[record.authority_tier for record in overlapping],
                effective_periods=[
                    EffectivePeriod(
                        effective_from=record.effective_from,
                        effective_to=record.effective_to,
                    )
                    for record in overlapping
                ],
                suggested_review_action=(
                    "Compare source authority, scope, and effective dates; "
                    "resolve each differing field."
                ),
            )
        )
    return conflicts
