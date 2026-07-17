from scripts.ingest_uw_sample import run_fixture_sample


def test_fixture_sample_publishes_only_evidenced_records(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'sample.db').as_posix()}"

    summary = run_fixture_sample(database_url)

    assert summary.pages_processed >= 6
    assert summary.records_published > 0
    assert summary.records_without_evidence == 0
    assert summary.fatal_errors == []
