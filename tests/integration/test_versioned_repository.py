from sqlalchemy.ext.asyncio import AsyncSession

from academic_ingest.db.repositories import VersionRepository, compute_changed_blocks


async def test_record_publication_is_idempotent_and_append_versioned(
    db_session: AsyncSession,
) -> None:
    repository = VersionRepository(db_session)

    first = await repository.publish(
        record_type="course",
        canonical_key="uw-seattle:CSE:123",
        payload={"title": "Programming III", "credits": 4},
    )
    duplicate = await repository.publish(
        record_type="course",
        canonical_key="uw-seattle:CSE:123",
        payload={"credits": 4, "title": "Programming III"},
    )
    changed = await repository.publish(
        record_type="course",
        canonical_key="uw-seattle:CSE:123",
        payload={"title": "Programming III", "credits": 5},
    )
    versions = await repository.list_versions("course", "uw-seattle:CSE:123")

    assert duplicate.id == first.id
    assert changed.id != first.id
    assert [version.version_number for version in versions] == [1, 2]
    assert versions[0].superseded is True
    assert versions[1].superseded is False
    assert (await repository.current("course", "uw-seattle:CSE:123")).id == changed.id


def test_changed_blocks_report_replaced_lines() -> None:
    changes = compute_changed_blocks(b"grade 2.0\ncredits 90", b"grade 2.5\ncredits 90")

    assert len(changes) == 1
    assert changes[0].previous == ["grade 2.0"]
    assert changes[0].current == ["grade 2.5"]
