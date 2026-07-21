from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol
from urllib.parse import urlsplit
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from academic_ingest.adapters.base import AdapterContext
from academic_ingest.api.app import build_default_adapter_registry
from academic_ingest.api.dependencies import ensure_institution
from academic_ingest.classification.page_classifier import PageClassifier
from academic_ingest.config.settings import InstitutionConfig, load_institution_config
from academic_ingest.db.base import Base
from academic_ingest.db.models import CrawlJobModel
from academic_ingest.db.repositories import SourceRepository
from academic_ingest.db.session import create_engine_and_session
from academic_ingest.discovery.robots import RobotsPolicy
from academic_ingest.extraction.fake_client import FakeStructuredExtractionClient
from academic_ingest.fetching.client import FetchOutcome, FetchResult, SafeFetchClient
from academic_ingest.jobs.ingest_job import run_ingest_job
from academic_ingest.models.domain import EvidenceBackedRecord, SourcePage
from academic_ingest.models.enums import JobStatus
from academic_ingest.observability import log_pipeline_summary
from academic_ingest.publishing.service import PublishingService
from academic_ingest.runtime import run_sync

# Curated course-catalog subjects backing the Bellevue -> UW transfer equivalencies.
COURSE_CATALOG_SUBJECTS = (
    "math",
    "engl",
    "econ",
    "psych",
    "anth",
    "archy",
    "art",
    "arthis",
    "cse",
    "info",
)


class LiveFetcher(Protocol):
    """Duck-typed subset of SafeFetchClient that _run_live depends on."""

    async def __aenter__(self) -> LiveFetcher: ...

    async def __aexit__(self, *args: object) -> None: ...

    async def fetch(self, url: str, crawl_job_id: UUID) -> FetchResult: ...


class SkippedSource(BaseModel):
    url: str
    reason: str


class LiveIngestionSummary(BaseModel):
    crawl_job_id: str
    pages_processed: int = Field(ge=0)
    records_extracted: int = Field(ge=0)
    records_published: int = Field(ge=0)
    records_rejected: int = Field(ge=0)
    records_without_evidence: int = Field(ge=0)
    review_tasks_created: int = Field(ge=0)
    conflicts_detected: int = Field(ge=0)
    warning_codes: list[str] = Field(default_factory=list)
    fatal_errors: list[str] = Field(default_factory=list)
    skipped: list[SkippedSource] = Field(default_factory=list)


def default_live_urls(config: InstitutionConfig) -> list[str]:
    """Institution seed URLs plus the curated course-catalog subject pages, deduplicated."""

    candidates = [
        *config.seed_urls,
        *(
            f"https://www.washington.edu/students/crscat/{subject}.html"
            for subject in COURSE_CATALOG_SUBJECTS
        ),
    ]
    seen: set[str] = set()
    deduplicated: list[str] = []
    for url in candidates:
        if url not in seen:
            seen.add(url)
            deduplicated.append(url)
    return deduplicated


async def _run_live(
    urls: Sequence[str],
    *,
    contact_email: str,
    config_path: Path | str,
    database_url: str,
    fetcher: LiveFetcher | None = None,
) -> LiveIngestionSummary:
    config = load_institution_config(config_path)
    engine, session_factory = create_engine_and_session(database_url)
    if database_url.startswith("sqlite+"):
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    client = fetcher if fetcher is not None else SafeFetchClient(
        config, contact_email=contact_email, network_enabled=True
    )

    try:
        async with client as active_client, session_factory() as session:
            await ensure_institution(session, config)
            job = CrawlJobModel(
                id=uuid4(),
                institution_id=config.institution_id,
                started_at=datetime.now(UTC),
                status=JobStatus.RUNNING.value,
                configuration={"live": True, "urls": list(urls)},
                parser_versions={},
                warnings=[],
                errors=[],
            )
            session.add(job)
            await session.commit()

            classifier = PageClassifier()
            sources = SourceRepository(session)
            contexts: list[AdapterContext] = []
            snapshots: dict = {}
            skipped: list[SkippedSource] = []
            robots_cache: dict[str, RobotsPolicy | None] = {}

            for url in urls:
                if not config.is_allowed_url(url):
                    skipped.append(
                        SkippedSource(url=url, reason="source_outside_configured_scope")
                    )
                    continue

                parsed = urlsplit(url)
                origin = f"{parsed.scheme}://{parsed.netloc}"
                if origin not in robots_cache:
                    robots_result = await active_client.fetch(f"{origin}/robots.txt", job.id)
                    if robots_result.outcome == FetchOutcome.FETCHED and robots_result.content:
                        robots_cache[origin] = RobotsPolicy.from_text(
                            f"{origin}/robots.txt",
                            robots_result.content.decode("utf-8", errors="replace"),
                            user_agent=config.request_policy.build_user_agent(contact_email),
                        )
                    else:
                        robots_cache[origin] = None
                robots = robots_cache[origin]
                if robots is None:
                    skipped.append(
                        SkippedSource(url=url, reason="robots_unavailable_fail_closed")
                    )
                    continue
                decision = robots.evaluate(url)
                if not decision.allowed:
                    skipped.append(SkippedSource(url=url, reason="robots_disallowed"))
                    continue

                try:
                    fetched = await active_client.fetch(url, job.id)
                except Exception as error:
                    skipped.append(
                        SkippedSource(url=url, reason=f"{type(error).__name__}: {error}")
                    )
                    continue

                if fetched.outcome != FetchOutcome.FETCHED or fetched.content is None:
                    reason = fetched.skip_reason or fetched.outcome.value
                    skipped.append(SkippedSource(url=url, reason=reason))
                    continue

                content_type = (fetched.content_type or "").split(";", 1)[0].strip().lower()
                if not content_type.startswith("text/html"):
                    skipped.append(
                        SkippedSource(
                            url=url,
                            reason=f"non_html_content_type:{content_type or 'unknown'}",
                        )
                    )
                    continue

                raw = fetched.content
                source_url = fetched.final_url
                page = classifier.classify(source_url, raw, content_type=content_type)
                source_page = SourcePage(
                    institution_id=config.institution_id,
                    canonical_url=url,
                    final_url=source_url,
                    page_title=page.title,
                    source_type=page.source_type,
                    policy_family=page.policy_family,
                    campus=config.campus,
                    http_status=fetched.status_code or 200,
                    content_type=content_type,
                )
                stored_page = await sources.upsert_page(source_page)
                snapshot = await sources.create_snapshot(
                    stored_page.id,
                    raw,
                    job.id,
                    response_headers=fetched.response_headers
                    or {"content-type": content_type},
                    parser_version="live-ingest-v1",
                    raw_content_location=source_url,
                )
                snapshots[snapshot.id] = raw
                contexts.append(
                    AdapterContext(
                        page=page,
                        raw_content=raw,
                        source_snapshot_id=snapshot.id,
                        crawl_job_id=job.id,
                        institution_id=config.institution_id,
                        campus=config.campus,
                        source_page_id=stored_page.id,
                    )
                )

            pipeline = await run_ingest_job(
                contexts,
                extraction_client=FakeStructuredExtractionClient(),
                adapter_registry=build_default_adapter_registry(),
            )
            candidates = [
                record
                for record in pipeline.records
                if isinstance(record, EvidenceBackedRecord)
            ]
            publication = await PublishingService(
                session,
                snapshots=snapshots,
            ).publish(candidates)
            job.completed_at = datetime.now(UTC)
            job.status = (
                JobStatus.PARTIAL.value
                if pipeline.errors or publication.rejected_record_ids or skipped
                else JobStatus.COMPLETED.value
            )
            job.pages_discovered = len(urls)
            job.pages_fetched = len(contexts)
            job.records_created = len(publication.published)
            job.warnings = [
                f"{warning.code}: {warning.message}" for warning in pipeline.warnings
            ]
            job.errors = [f"{error.code}: {error.message}" for error in pipeline.errors]
            await session.commit()
            log_pipeline_summary(pipeline, job.id)
            return LiveIngestionSummary(
                crawl_job_id=str(job.id),
                pages_processed=len(contexts),
                records_extracted=len(candidates),
                records_published=len(publication.published),
                records_rejected=len(publication.rejected_record_ids),
                records_without_evidence=sum(
                    not version.evidence_record_ids for version in publication.published
                ),
                review_tasks_created=len(publication.review_tasks),
                conflicts_detected=len(publication.conflicts),
                warning_codes=[warning.code for warning in pipeline.warnings],
                fatal_errors=[error.message for error in pipeline.errors],
                skipped=skipped,
            )
    finally:
        await engine.dispose()


def run_live_ingestion(
    urls: Sequence[str] | None,
    allow_network: bool,
    *,
    contact_email: str | None = None,
    config_path: Path | str = "config/institutions/uw_seattle.yaml",
    database_url: str,
    fetcher: LiveFetcher | None = None,
) -> LiveIngestionSummary:
    if not allow_network:
        raise ValueError("live ingestion requires --allow-network")
    resolved_contact = (contact_email or os.getenv("ACADEMIC_INGEST_CONTACT_EMAIL", "")).strip()
    if not resolved_contact:
        raise ValueError("ACADEMIC_INGEST_CONTACT_EMAIL is required for live ingestion")
    config = load_institution_config(config_path)
    resolved_urls = list(urls) if urls else default_live_urls(config)
    deduplicated_urls = list(dict.fromkeys(resolved_urls))
    return run_sync(
        _run_live(
            deduplicated_urls,
            contact_email=resolved_contact,
            config_path=config_path,
            database_url=database_url,
            fetcher=fetcher,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest live UW Seattle pages")
    parser.add_argument(
        "urls", nargs="*", help="Live UW URLs; defaults to seed_urls + course-catalog subjects"
    )
    parser.add_argument(
        "--allow-network",
        action="store_true",
        required=True,
        help="Required opt-in for live network fetching",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="Overrides ACADEMIC_INGEST_DATABASE_URL",
    )
    parser.add_argument(
        "--config",
        default="config/institutions/uw_seattle.yaml",
        help="Institution configuration path",
    )
    args = parser.parse_args()

    from academic_ingest.config.settings import Settings

    settings = Settings(database_url=args.database_url) if args.database_url else Settings()
    summary = run_live_ingestion(
        args.urls or None,
        args.allow_network,
        config_path=args.config,
        database_url=settings.database_url,
    )
    print(json.dumps(summary.model_dump(mode="json"), indent=2))
    return 0 if not summary.fatal_errors and summary.records_without_evidence == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
