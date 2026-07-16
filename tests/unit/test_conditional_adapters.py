from uuid import uuid4

from academic_ingest.adapters.base import AdapterContext
from academic_ingest.adapters.uw.equivalency_guide import EquivalencyGuideAdapter
from academic_ingest.adapters.uw.time_schedule import TimeScheduleAdapter
from academic_ingest.classification.page_classifier import PageClassifier


def make_context(url: str, html: bytes) -> AdapterContext:
    return AdapterContext(
        page=PageClassifier().classify(url, html, content_type="text/html"),
        raw_content=html,
        source_snapshot_id=uuid4(),
        crawl_job_id=uuid4(),
        institution_id="uw-seattle",
        campus="Seattle",
    )


def test_time_schedule_does_not_follow_netid_only_links() -> None:
    html = b"""
    <h1>Time Schedule</h1>
    <a href="/students/timeschd/AUT2026/">Course Offerings</a>
    <a href="https://sdb.admin.uw.edu/timeschd/uwnetid/sln.asp">NetID required</a>
    """

    result = TimeScheduleAdapter().extract(
        make_context("https://www.washington.edu/students/timeschd/", html)
    )

    assert result.records == []
    assert result.discovered_links == ["https://www.washington.edu/students/timeschd/AUT2026/"]
    assert any("NetID" in warning.message for warning in result.warnings)


def test_equivalency_guide_is_discovery_only() -> None:
    html = b'<a href="/apply/transfer/equivalency-guide/bellevue-college/">Bellevue</a>'

    result = EquivalencyGuideAdapter().extract(
        make_context(
            "https://admit.washington.edu/apply/transfer/equivalency-guide/",
            html,
        )
    )

    assert result.records == []
    assert result.discovered_links == [
        "https://admit.washington.edu/apply/transfer/equivalency-guide/bellevue-college/"
    ]
    assert any("mapping" in warning.message.lower() for warning in result.warnings)
