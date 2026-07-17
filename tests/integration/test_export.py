import json

from scripts.export_uw_records import export_records
from scripts.ingest_uw_sample import run_fixture_sample


def test_export_excludes_raw_snapshot_bytes(tmp_path) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'export.db').as_posix()}"
    run_fixture_sample(database_url)

    payload = export_records(database_url)
    serialized = json.dumps(payload)

    assert payload["schema_version"] == "1.0"
    assert payload["institution_id"] == "uw-seattle"
    assert payload["records"]
    assert any(record["record_type"] == "exam_credit_rule" for record in payload["records"])
    assert "raw_content" not in serialized
    assert "<!doctype html>" not in serialized.lower()
