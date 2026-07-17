from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from academic_ingest.api.app import create_app
from academic_ingest.config.settings import Settings
from academic_ingest.db.models import ReviewTaskModel
from academic_ingest.validation.evidence import validate_evidence


@pytest.fixture
def client() -> TestClient:
    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        network_enabled=False,
        institution_config_path=Path("config/institutions/uw_seattle.yaml"),
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def _ingest_course_fixture(client: TestClient) -> dict:
    html = Path("tests/fixtures/uw/html/courses_cse.html").read_bytes()
    response = client.post(
        "/pages/ingest",
        data={"source_url": "https://www.washington.edu/students/crscat/cse.html"},
        files={"file": ("courses_cse.html", html, "text/html")},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_health_reports_database(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok", "network_enabled": False}


def test_local_fixture_ingest_publishes_evidenced_records(client: TestClient) -> None:
    payload = _ingest_course_fixture(client)

    assert payload["records_extracted"] >= 1
    assert payload["records_published"] >= 1
    assert payload["errors"] == []
    assert payload["source_page_id"]
    assert payload["source_snapshot_id"]


def test_course_filters_and_detail_include_evidence_and_versions(client: TestClient) -> None:
    _ingest_course_fixture(client)

    listing = client.get("/courses", params={"subject": "CSE", "number": "143"})
    assert listing.status_code == 200
    items = listing.json()["items"]
    assert len(items) == 1
    assert items[0]["canonical_code"] == "CSE 143"

    detail = client.get(f"/courses/{items[0]['id']}")
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["evidence"]
    fixture = Path("tests/fixtures/uw/html/courses_cse.html").read_bytes()
    assert validate_evidence(payload["evidence"][0]["evidence_text"], fixture).accepted
    assert len(payload["versions"]) == 1


def test_source_detail_includes_snapshot_history(client: TestClient) -> None:
    ingested = _ingest_course_fixture(client)

    detail = client.get(f"/sources/{ingested['source_page_id']}")

    assert detail.status_code == 200
    assert detail.json()["canonical_url"].endswith("/students/crscat/cse.html")
    assert len(detail.json()["snapshots"]) == 1


def test_crawl_job_is_bounded_to_configured_uw_sources(client: TestClient) -> None:
    accepted = client.post(
        "/crawl-jobs",
        json={
            "urls": ["https://www.washington.edu/students/crscat/"],
            "allow_network": False,
        },
    )
    rejected = client.post(
        "/crawl-jobs",
        json={"urls": ["https://example.com/policy"], "allow_network": False},
    )

    assert accepted.status_code == 201
    job = client.get(f"/crawl-jobs/{accepted.json()['id']}")
    assert job.status_code == 200
    assert job.json()["status"] == "queued"
    assert rejected.status_code == 422


def test_policy_and_governance_collection_endpoints_are_available(client: TestClient) -> None:
    for path in [
        "/programs",
        "/admissions-rules",
        "/transfer-policies",
        "/exam-credit",
        "/conflicts",
        "/review-tasks",
        "/sources",
    ]:
        response = client.get(path)
        assert response.status_code == 200, path
        assert "items" in response.json()


def test_resolving_unknown_review_task_returns_not_found(client: TestClient) -> None:
    response = client.post(
        f"/review-tasks/{uuid4()}/resolve",
        json={
            "status": "resolved",
            "reviewer": "api-test",
            "rationale": "Verified against the registrar source.",
        },
    )

    assert response.status_code == 404


def test_review_resolution_records_metadata_without_mutating_evidence(
    client: TestClient,
) -> None:
    _ingest_course_fixture(client)
    course = client.get("/courses", params={"subject": "CSE", "number": "143"}).json()["items"][0]
    evidence_before = client.get(f"/courses/{course['id']}").json()["evidence"]

    async def seed_review_task() -> str:
        async with client.app.state.session_factory() as session:
            task = ReviewTaskModel(
                institution_id="uw-seattle",
                record_type="course",
                record_id=UUID(course["id"]),
                reason="unclear_catalog_year",
                severity="warning",
                unresolved_question="Which catalog year governs this record?",
                status="pending",
            )
            session.add(task)
            await session.commit()
            return str(task.id)

    assert client.portal is not None
    task_id = client.portal.call(seed_review_task)
    response = client.post(
        f"/review-tasks/{task_id}/resolve",
        json={
            "status": "resolved",
            "reviewer": "api-test",
            "rationale": "The catalog page is current for the fixture period.",
        },
    )

    assert response.status_code == 200
    assert response.json()["resolution"]["reviewer"] == "api-test"
    assert client.get(f"/courses/{course['id']}").json()["evidence"] == evidence_before
