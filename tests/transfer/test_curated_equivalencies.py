"""Tests for the curated, CITED transfer-equivalency dataset.

These tests check the SHAPE of the curated data (every record is cited, every
mapping_type is a valid DB spelling, the primary Bellevue pathway is populated)
and that the data is correctly wired into the real `/transfer/outcomes` endpoint
default repository. The data-content correctness itself is established by the
citations in `docs/equivalencies/SOURCES.md`, not asserted here.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from academic_ingest.api.app import create_app
from academic_ingest.config.settings import Settings
from academic_ingest.models.transfer_state import SUPABASE_MAPPING_TYPE_TO_STATE
from academic_ingest.transfer.curated_equivalencies import curated_records


def test_curated_records_returns_a_dict() -> None:
    records = curated_records()
    assert isinstance(records, dict)


def test_every_curated_record_is_cited_and_uses_a_valid_mapping_type() -> None:
    records = curated_records()
    assert records, "curated_records() must not be empty"

    for (source_id, destination_id), record_list in records.items():
        assert isinstance(source_id, str) and source_id
        assert isinstance(destination_id, str) and destination_id
        assert record_list, f"no records for ({source_id}, {destination_id})"

        for record in record_list:
            assert record.evidence_refs, (
                f"record for {record.source_course_codes} has no evidence_refs "
                "(every mapping must be cited)"
            )
            assert record.mapping_type in SUPABASE_MAPPING_TYPE_TO_STATE, (
                f"record for {record.source_course_codes} has invalid "
                f"mapping_type {record.mapping_type!r}"
            )


def test_bellevue_college_pathway_has_at_least_one_record() -> None:
    records = curated_records()
    bellevue_records = records.get(("bellevue-college", "uw-seattle"), [])
    assert len(bellevue_records) >= 1


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A TestClient with NO dependency override, so /transfer/outcomes uses the
    real curated default repository built from curated_records()."""
    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        network_enabled=False,
        institution_config_path=Path("config/institutions/uw_seattle.yaml"),
    )
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client


def test_real_bellevue_course_resolves_to_a_non_not_found_state(client: TestClient) -> None:
    # CS 101 -> UW CSE 100, per the official UW Office of Admissions Bellevue
    # College Equivalency Guide (see docs/equivalencies/SOURCES.md).
    response = client.post(
        "/transfer/outcomes",
        json={
            "pathway_key": "bellevue-college:uw-seattle",
            "courses": [{"code": "CS 101", "title": "Computer Science I"}],
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    outcome = payload["outcomes"][0]
    assert outcome["state"] != "not_found"
    assert outcome["state"] == "direct_equivalent"
    assert outcome["evidence_refs"], "resolved outcome must carry the citation forward"


def test_nonsense_course_code_resolves_to_not_found(client: TestClient) -> None:
    response = client.post(
        "/transfer/outcomes",
        json={
            "pathway_key": "bellevue-college:uw-seattle",
            "courses": [{"code": "ZZZZ 9999", "title": "Not a real course"}],
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    outcome = payload["outcomes"][0]
    assert outcome["state"] == "not_found"
