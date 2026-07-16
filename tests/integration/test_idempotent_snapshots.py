from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from academic_ingest.db.models import (
    CrawlJobModel,
    InstitutionModel,
    SourceChangeEventModel,
    SourceSnapshotModel,
)
from academic_ingest.db.repositories import SourceRepository
from academic_ingest.models.domain import SourcePage
from academic_ingest.models.enums import CalendarSystem, JobStatus, PolicyFamily, SourceType


async def seed_source_page(db_session: AsyncSession) -> tuple[SourceRepository, SourcePage, str]:
    institution = InstitutionModel(
        id="uw-seattle",
        legal_name="University of Washington",
        common_name="University of Washington",
        campus="Seattle",
        state="Washington",
        country="US",
        calendar_system=CalendarSystem.QUARTER.value,
        official_domains=["www.washington.edu", "admit.washington.edu"],
    )
    crawl_id = uuid4()
    db_session.add_all(
        [
            institution,
            CrawlJobModel(
                id=crawl_id,
                institution_id=institution.id,
                status=JobStatus.RUNNING.value,
            ),
        ]
    )
    await db_session.commit()

    page = SourcePage(
        institution_id=institution.id,
        canonical_url="https://www.washington.edu/students/crscat/cse.html",
        final_url="https://www.washington.edu/students/crscat/cse.html",
        page_title="COMPUTER SCIENCE & ENGINEERING",
        source_type=SourceType.COURSE_CATALOG,
        policy_family=PolicyFamily.COURSE,
        campus="Seattle",
        http_status=200,
        content_type="text/html",
    )
    repository = SourceRepository(db_session)
    stored_page = await repository.upsert_page(page)
    page.id = stored_page.id
    return repository, page, str(crawl_id)


async def test_identical_snapshot_is_idempotent(db_session: AsyncSession) -> None:
    repository, page, crawl_id = await seed_source_page(db_session)

    first = await repository.create_snapshot(page.id, b"same body", crawl_id)
    second = await repository.create_snapshot(page.id, b"same body", crawl_id)
    count = await db_session.scalar(select(func.count()).select_from(SourceSnapshotModel))

    assert first.id == second.id
    assert count == 1


async def test_changed_snapshot_preserves_previous_version(db_session: AsyncSession) -> None:
    repository, page, crawl_id = await seed_source_page(db_session)

    first = await repository.create_snapshot(page.id, b"first", crawl_id)
    second = await repository.create_snapshot(page.id, b"second", crawl_id)
    snapshots = await repository.list_snapshots(page.id)

    assert first.id != second.id
    assert [item.raw_content_hash for item in snapshots] == [
        first.raw_content_hash,
        second.raw_content_hash,
    ]


async def test_snapshot_accepts_durable_content_location(db_session: AsyncSession) -> None:
    repository, page, crawl_id = await seed_source_page(db_session)

    snapshot = await repository.create_snapshot(
        page.id,
        b"stored body",
        crawl_id,
        raw_content_location="file:///var/snapshots/body.html",
    )

    assert snapshot.raw_content_location == "file:///var/snapshots/body.html"


async def test_change_event_uses_previous_raw_content(db_session: AsyncSession) -> None:
    repository, page, crawl_id = await seed_source_page(db_session)
    previous = b"grade 2.0\ncredits 90"
    current = b"grade 2.5\ncredits 90"
    first = await repository.create_snapshot(page.id, previous, crawl_id)

    second = await repository.create_snapshot(
        page.id,
        current,
        crawl_id,
        previous_raw_content=previous,
    )
    event = await db_session.scalar(select(SourceChangeEventModel))

    assert event is not None
    assert event.previous_snapshot_id == first.id
    assert event.current_snapshot_id == second.id
    assert event.changed_blocks[0]["previous"] == ["grade 2.0"]
    assert event.changed_blocks[0]["current"] == ["grade 2.5"]
