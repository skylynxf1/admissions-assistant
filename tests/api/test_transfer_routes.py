"""Tests for the /transfer/outcomes API endpoint.

Uses TestClient with a dependency override for get_equivalency_repository so the
route is exercised end-to-end without touching real institutional data.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from academic_ingest.api.app import create_app
from academic_ingest.api.routes.transfer import get_equivalency_repository
from academic_ingest.config.settings import Settings
from academic_ingest.transfer.models import EquivalencyRecord
from academic_ingest.transfer.repository import InMemoryEquivalencyRepository


@pytest.fixture
def client() -> Iterator[TestClient]:
    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        network_enabled=False,
        institution_config_path=Path("config/institutions/uw_seattle.yaml"),
    )
    app = create_app(settings)
    records = {
        ("bellevue-college", "uw-seattle"): [
            EquivalencyRecord(
                source_course_codes=["SRC 101"],
                mapping_type="direct_equivalent",
                destination_outcome="UW TEST 101",
                evidence_refs=["ev-direct"],
            )
        ],
    }
    app.dependency_overrides[get_equivalency_repository] = lambda: InMemoryEquivalencyRepository(
        records
    )
    with TestClient(app) as test_client:
        yield test_client


def test_post_outcomes_returns_direct_match_for_known_pathway(client: TestClient) -> None:
    response = client.post(
        "/transfer/outcomes",
        json={
            "pathway_key": "bellevue-college:uw-seattle",
            "courses": [{"code": "SRC 101", "title": "Synthetic Intro Course"}],
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["pathway_key"] == "bellevue-college:uw-seattle"
    assert payload["source_institution_id"] == "bellevue-college"
    assert payload["destination_institution_id"] == "uw-seattle"
    assert payload["outcomes"][0]["state"] == "direct_equivalent"
    assert payload["outcomes"][0]["destination_outcomes"] == ["UW TEST 101"]


def test_post_outcomes_unknown_pathway_returns_404(client: TestClient) -> None:
    response = client.post(
        "/transfer/outcomes",
        json={"pathway_key": "bogus:pathway", "courses": [{"code": "SRC 101"}]},
    )

    assert response.status_code == 404


@pytest.fixture
def default_client() -> Iterator[TestClient]:
    """A TestClient with NO dependency override, so /transfer/outcomes uses the
    real default repository built from the parsed Bellevue guide."""
    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        network_enabled=False,
        institution_config_path=Path("config/institutions/uw_seattle.yaml"),
    )
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client


def test_default_repository_resolves_a_real_bellevue_course(default_client: TestClient) -> None:
    # Real row from the bundled guide snapshot: "ENGL& 101" -> "ENGL 131 (5)".
    response = default_client.post(
        "/transfer/outcomes",
        json={
            "pathway_key": "bellevue-college:uw-seattle",
            "courses": [{"code": "ENGL& 101", "title": "English Composition I"}],
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    outcome = payload["outcomes"][0]
    assert outcome["state"] == "direct_equivalent"
    assert outcome["evidence_refs"], "resolved outcome must carry the citation forward"


def test_default_repository_reports_not_found_for_a_nonsense_course(
    default_client: TestClient,
) -> None:
    response = default_client.post(
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
