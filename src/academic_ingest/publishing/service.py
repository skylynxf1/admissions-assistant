from __future__ import annotations

from collections.abc import Mapping, Sequence
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from academic_ingest.confidence.rules import ConfidenceFactors
from academic_ingest.confidence.scorer import score_confidence
from academic_ingest.conflicts.detector import detect_conflicts
from academic_ingest.conflicts.models import canonical_record_key, record_type_name
from academic_ingest.db.models import (
    ConflictRecordModel,
    EvidenceRecordModel,
    RecordVersionModel,
    ReviewTaskModel,
)
from academic_ingest.db.repositories import VersionRepository
from academic_ingest.models.domain import ConflictRecord, EvidenceBackedRecord, ReviewTask
from academic_ingest.models.enums import Severity
from academic_ingest.review.service import review_task_for_issue
from academic_ingest.validation.evidence import validate_candidate
from academic_ingest.validation.models import ValidationIssue


class PublishResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    published: list[RecordVersionModel] = Field(default_factory=list)
    rejected_record_ids: list[UUID] = Field(default_factory=list)
    review_tasks: list[ReviewTask] = Field(default_factory=list)
    conflicts: list[ConflictRecord] = Field(default_factory=list)


class PublishingService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        snapshots: Mapping[UUID, bytes],
    ) -> None:
        self.session = session
        self.snapshots = snapshots
        self.repository = VersionRepository(session)

    async def publish(self, batch: Sequence[EvidenceBackedRecord]) -> PublishResult:
        result = PublishResult()
        conflicts = detect_conflicts(batch)
        result.conflicts = conflicts
        conflicting_ids = {record_id for conflict in conflicts for record_id in conflict.record_ids}
        try:
            for conflict in conflicts:
                self.session.add(
                    ConflictRecordModel(
                        id=conflict.id,
                        institution_id=conflict.institution_id,
                        record_type=conflict.record_type,
                        record_ids=[str(item) for item in conflict.record_ids],
                        conflict_type=conflict.conflict_type,
                        differing_fields=conflict.model_dump(mode="json")["differing_fields"],
                        source_authorities=[str(item) for item in conflict.source_authorities],
                        effective_periods=conflict.model_dump(mode="json")["effective_periods"],
                        detected_at=conflict.detected_at,
                        status=conflict.status,
                        suggested_review_action=conflict.suggested_review_action,
                    )
                )
            for record in batch:
                validation = validate_candidate(record, self.snapshots)
                conflict_count = sum(record.id in conflict.record_ids for conflict in conflicts)
                exact_evidence = bool(record.evidence) and not any(
                    issue.code
                    in {"missing_exact_evidence", "evidence_not_found", "snapshot_not_available"}
                    for issue in validation.issues
                )
                official_source = exact_evidence and not any(
                    issue.code in {"source_outside_official_scope", "campus_out_of_scope"}
                    for issue in validation.issues
                )
                factors = ConfidenceFactors(
                    official_source=official_source,
                    exact_evidence=exact_evidence,
                    deterministic_parser="gpt" not in record.parser_name.casefold(),
                    schema_valid=validation.accepted,
                    current_or_dated=bool(
                        record.effective_from
                        or record.effective_to
                        or any(evidence.catalog_year for evidence in record.evidence)
                    ),
                    corroborated=len(record.evidence) > 1,
                    ambiguous=bool(record.warnings),
                    unresolved_field_count=len(record.unresolved_fields),
                    conflict_count=conflict_count,
                    material_change="material_change" in record.warnings,
                )
                confidence = score_confidence(factors)
                record.confidence_tier = confidence.tier
                if (
                    not validation.accepted
                    or not confidence.publishable
                    or record.id in conflicting_ids
                ):
                    result.rejected_record_ids.append(record.id)
                    issues = [
                        issue
                        for issue in validation.issues
                        if issue.disposition in {"review", "block_publish"}
                    ]
                    if not issues:
                        reason = (
                            confidence.blocking_reasons[0]
                            if confidence.blocking_reasons
                            else "review"
                        )
                        issues = [
                            ValidationIssue(
                                code="confidence_review_required",
                                message=reason,
                                severity=Severity.WARNING,
                                disposition="review",
                            )
                        ]
                    for issue in issues:
                        task = review_task_for_issue(record, issue)
                        result.review_tasks.append(task)
                        self.session.add(ReviewTaskModel(**task.model_dump(mode="python")))
                    continue

                payload = record.model_dump(
                    mode="json",
                    exclude={
                        "id",
                        "evidence",
                        "crawl_job_id",
                        "confidence_tier",
                        "review_status",
                    },
                )
                version = await self.repository.publish(
                    record_type=record_type_name(record),
                    canonical_key=canonical_record_key(record),
                    payload=payload,
                    evidence_record_ids=[evidence.id for evidence in record.evidence],
                    commit=False,
                )
                retained_evidence_ids = set(version.evidence_record_ids)
                for evidence in record.evidence:
                    if str(evidence.id) not in retained_evidence_ids:
                        continue
                    stored_evidence = await self.session.get(EvidenceRecordModel, evidence.id)
                    if stored_evidence is None:
                        self.session.add(
                            EvidenceRecordModel(**evidence.model_dump(mode="python"))
                        )
                result.published.append(version)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return result
