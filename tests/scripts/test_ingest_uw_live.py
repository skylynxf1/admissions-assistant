from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest

from academic_ingest.fetching.client import FetchOutcome, FetchResult
from scripts.ingest_uw_live import run_live_ingestion

CSE_URL = "https://www.washington.edu/students/crscat/cse.html"
DISALLOWED_URL = "https://example.com/not-an-official-uw-source"
ROBOTS_ALLOW_ALL = b"User-agent: *\nAllow: /\n"


class FakeLiveFetcher:
    """Offline stand-in for SafeFetchClient: serves canned bytes, never touches the network."""

    def __init__(self, pages: dict[str, bytes], *, robots_text: bytes = ROBOTS_ALLOW_ALL) -> None:
        self.pages = pages
        self.robots_text = robots_text
        self.requested_urls: list[str] = []

    async def __aenter__(self) -> FakeLiveFetcher:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def fetch(self, url: str, crawl_job_id: UUID) -> FetchResult:
        self.requested_urls.append(url)
        if url.endswith("/robots.txt"):
            return FetchResult(
                crawl_job_id=crawl_job_id,
                request_url=url,
                final_url=url,
                outcome=FetchOutcome.FETCHED,
                status_code=200,
                content=self.robots_text,
                content_type="text/plain",
            )
        content = self.pages.get(url)
        if content is None:
            return FetchResult(
                crawl_job_id=crawl_job_id,
                request_url=url,
                final_url=url,
                outcome=FetchOutcome.FAILED,
                status_code=404,
                skip_reason="HTTP 404",
            )
        return FetchResult(
            crawl_job_id=crawl_job_id,
            request_url=url,
            final_url=url,
            outcome=FetchOutcome.FETCHED,
            status_code=200,
            content=content,
            content_type="text/html",
        )


def _scratch_db_url(tmp_path: Path) -> str:
    return f"sqlite+aiosqlite:///{(tmp_path / 'live.db').as_posix()}"


def test_allow_network_false_does_not_fetch(tmp_path: Path) -> None:
    fetcher = FakeLiveFetcher({CSE_URL: b"<html></html>"})

    with pytest.raises(ValueError, match="allow-network"):
        run_live_ingestion(
            [CSE_URL],
            False,
            contact_email="test@example.com",
            database_url=_scratch_db_url(tmp_path),
            fetcher=fetcher,
        )

    assert fetcher.requested_urls == []


def test_missing_contact_email_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ACADEMIC_INGEST_CONTACT_EMAIL", raising=False)
    fetcher = FakeLiveFetcher({CSE_URL: b"<html></html>"})

    with pytest.raises(ValueError, match="CONTACT_EMAIL"):
        run_live_ingestion(
            [CSE_URL],
            True,
            contact_email="",
            database_url=_scratch_db_url(tmp_path),
            fetcher=fetcher,
        )

    assert fetcher.requested_urls == []


def test_injected_fetcher_runs_pipeline_offline_and_publishes(tmp_path: Path) -> None:
    fixture = Path("tests/fixtures/uw/html/courses_cse.html").read_bytes()
    fetcher = FakeLiveFetcher({CSE_URL: fixture})

    summary = run_live_ingestion(
        [CSE_URL],
        True,
        contact_email="test@example.com",
        database_url=_scratch_db_url(tmp_path),
        fetcher=fetcher,
    )

    assert summary.pages_processed == 1
    assert summary.records_published >= 1
    assert summary.fatal_errors == []
    assert summary.skipped == []
    # robots.txt + the page itself, no other network traffic.
    assert set(fetcher.requested_urls) == {
        "https://www.washington.edu/robots.txt",
        CSE_URL,
    }


def test_disallowed_url_is_skipped_and_never_fetched(tmp_path: Path) -> None:
    fetcher = FakeLiveFetcher({DISALLOWED_URL: b"<html></html>"})

    summary = run_live_ingestion(
        [DISALLOWED_URL],
        True,
        contact_email="test@example.com",
        database_url=_scratch_db_url(tmp_path),
        fetcher=fetcher,
    )

    assert summary.pages_processed == 0
    assert len(summary.skipped) == 1
    assert summary.skipped[0].url == DISALLOWED_URL
    assert summary.skipped[0].reason == "source_outside_configured_scope"
    assert fetcher.requested_urls == []
