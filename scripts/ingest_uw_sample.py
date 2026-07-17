from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from academic_ingest.adapters.base import AdapterContext
from academic_ingest.api.app import build_default_adapter_registry
from academic_ingest.api.dependencies import ensure_institution
from academic_ingest.classification.page_classifier import PageClassifier
from academic_ingest.config.settings import load_institution_config
from academic_ingest.db.base import Base
from academic_ingest.db.models import CrawlJobModel
from academic_ingest.db.repositories import SourceRepository
from academic_ingest.db.session import create_engine_and_session
from academic_ingest.extraction.fake_client import FakeStructuredExtractionClient
from academic_ingest.jobs.ingest_job import run_ingest_job
from academic_ingest.models.domain import EvidenceBackedRecord, SourcePage
from academic_ingest.models.enums import JobStatus
from academic_ingest.observability import log_pipeline_summary
from academic_ingest.publishing.service import PublishingService
from academic_ingest.runtime import run_sync

FIXTURE_SOURCES = (
    ("course_glossary.html", "https://www.washington.edu/students/crscat/glossary.html"),
    ("courses_cse.html", "https://www.washington.edu/students/crscat/cse.html"),
    ("courses_info.html", "https://www.washington.edu/students/crscat/info.html"),
    ("majors_index.html", "https://admit.washington.edu/academics/majors/"),
    ("major_detail.html", "https://admit.washington.edu/majors/informatics/"),
    (
        "transfer_admissions.html",
        "https://admit.washington.edu/apply/transfer/how-to-apply/",
    ),
    ("transfer_policies.html", "https://admit.washington.edu/apply/transfer/policies/"),
    (
        "ap_credit.html",
        "https://admit.washington.edu/apply/transfer/exams-for-credit/ap/",
    ),
)


class FixtureIngestionSummary(BaseModel):
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


async def _run_fixture_sample(
    database_url: str,
    *,
    fixture_root: Path,
    config_path: Path | str,
) -> FixtureIngestionSummary:
    config = load_institution_config(config_path)
    engine, session_factory = create_engine_and_session(database_url)
    if database_url.startswith("sqlite+"):
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    try:
        async with session_factory() as session:
            await ensure_institution(session, config)
            job = CrawlJobModel(
                id=uuid4(),
                institution_id=config.institution_id,
                started_at=datetime.now(UTC),
                status=JobStatus.RUNNING.value,
                configuration={"fixture_only": True},
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
            for fixture_name, source_url in FIXTURE_SOURCES:
                fixture_path = fixture_root / fixture_name
                raw = fixture_path.read_bytes()
                page = classifier.classify(source_url, raw, content_type="text/html")
                source_page = SourcePage(
                    institution_id=config.institution_id,
                    canonical_url=source_url,
                    final_url=source_url,
                    page_title=page.title,
                    source_type=page.source_type,
                    policy_family=page.policy_family,
                    campus=config.campus,
                    http_status=200,
                    content_type="text/html",
                )
                stored_page = await sources.upsert_page(source_page)
                snapshot = await sources.create_snapshot(
                    stored_page.id,
                    raw,
                    job.id,
                    response_headers={"content-type": "text/html"},
                    parser_version="fixture-sample-v1",
                    raw_content_location=fixture_path.resolve().as_uri(),
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
                record for record in pipeline.records if isinstance(record, EvidenceBackedRecord)
            ]
            publication = await PublishingService(
                session,
                snapshots=snapshots,
            ).publish(candidates)
            job.completed_at = datetime.now(UTC)
            job.status = (
                JobStatus.PARTIAL.value
                if pipeline.errors or publication.rejected_record_ids
                else JobStatus.COMPLETED.value
            )
            job.pages_discovered = len(contexts)
            job.pages_fetched = len(contexts)
            job.records_created = len(publication.published)
            job.warnings = [f"{warning.code}: {warning.message}" for warning in pipeline.warnings]
            job.errors = [f"{error.code}: {error.message}" for error in pipeline.errors]
            await session.commit()
            log_pipeline_summary(pipeline, job.id)
            return FixtureIngestionSummary(
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
            )
    finally:
        await engine.dispose()


def run_fixture_sample(
    database_url: str,
    *,
    fixture_root: Path = Path("tests/fixtures/uw/html"),
    config_path: Path | str = "config/institutions/uw_seattle.yaml",
) -> FixtureIngestionSummary:
    return run_sync(
        _run_fixture_sample(
            database_url,
            fixture_root=fixture_root,
            config_path=config_path,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest the saved UW Seattle fixture sample")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fixture-only", action="store_true")
    mode.add_argument("--allow-network", action="store_true")
    parser.add_argument(
        "--database-url",
        default=None,
        help="Overrides ACADEMIC_INGEST_DATABASE_URL",
    )
    args = parser.parse_args()
    if args.allow_network:
        parser.error(
            "live acquisition is performed by inspect_uw_sources.py; "
            "ingestion requires reviewed snapshots"
        )
    from academic_ingest.config.settings import Settings

    settings = Settings(database_url=args.database_url) if args.database_url else Settings()
    summary = run_fixture_sample(settings.database_url)
    print(json.dumps(summary.model_dump(mode="json"), indent=2))
    return 0 if not summary.fatal_errors and summary.records_without_evidence == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
