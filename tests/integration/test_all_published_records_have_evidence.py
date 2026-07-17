from scripts.export_uw_records import export_records
from scripts.ingest_uw_sample import run_fixture_sample


def test_every_exported_record_has_resolvable_exact_evidence(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'evidence.db').as_posix()}"
    run_fixture_sample(database_url)

    payload = export_records(database_url)

    assert payload["records"]
    assert all(record["evidence"] for record in payload["records"])
    assert all(
        evidence["source_snapshot_id"]
        for record in payload["records"]
        for evidence in record["evidence"]
    )
