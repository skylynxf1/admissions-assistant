from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from academic_ingest.models.domain import Course, EvidenceRecord
from academic_ingest.models.enums import AuthorityTier, ConfidenceTier
from academic_ingest.publishing.service import PublishingService


def _course(snapshot_id: UUID, *, title: str = "Programming III") -> Course:
    evidence = EvidenceRecord(
        source_snapshot_id=snapshot_id,
        source_url="https://www.washington.edu/students/crscat/cse.html",
        page_title="Computer Science and Engineering",
        evidence_text="CSE 123",
        parser_name="course_catalog",
        parser_version="1.0",
        authority_tier=AuthorityTier.OFFICIAL_CATALOG,
        confidence_tier=ConfidenceTier.HIGH_CONFIDENCE,
    )
    return Course(
        institution_id="uw-seattle",
        subject="CSE",
        number="123",
        title=title,
        credits_min=Decimal("4"),
        credits_max=Decimal("4"),
        evidence=[evidence],
        parser_name="course_catalog",
        parser_version="1.0",
        authority_tier=AuthorityTier.OFFICIAL_CATALOG,
    )


async def test_policy_without_evidence_is_not_published(db_session: AsyncSession) -> None:
    snapshot_id = uuid4()
    candidate = _course(snapshot_id)
    candidate.evidence = []
    publisher = PublishingService(db_session, snapshots={snapshot_id: b"<p>CSE 123</p>"})

    result = await publisher.publish([candidate])

    assert result.published == []
    assert result.review_tasks[0].reason == "missing_exact_evidence"


async def test_publication_is_idempotent_and_appends_material_versions(
    db_session: AsyncSession,
) -> None:
    snapshot_id = uuid4()
    publisher = PublishingService(db_session, snapshots={snapshot_id: b"<p>CSE 123</p>"})
    first_candidate = _course(snapshot_id)

    first = await publisher.publish([first_candidate])
    duplicate = await publisher.publish([first_candidate])
    changed = await publisher.publish([_course(snapshot_id, title="Programming III revised")])

    assert first.published[0].id == duplicate.published[0].id
    assert changed.published[0].version_number == 2
    versions = await publisher.repository.list_versions("course", "uw-seattle:CSE 123")
    assert [version.version_number for version in versions] == [1, 2]
    assert versions[0].superseded is True
    assert versions[0].evidence_record_ids == [str(first_candidate.evidence[0].id)]


async def test_snapshot_mismatch_creates_review_instead_of_publish(
    db_session: AsyncSession,
) -> None:
    candidate = _course(uuid4())
    publisher = PublishingService(db_session, snapshots={uuid4(): b"<p>CSE 123</p>"})

    result = await publisher.publish([candidate])

    assert result.published == []
    assert result.review_tasks[0].reason == "snapshot_not_available"
