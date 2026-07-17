from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from academic_ingest.adapters.base import AdapterContext
from academic_ingest.api.dependencies import InstitutionConfigDep, SessionDep, ensure_institution
from academic_ingest.api.schemas.common import PageIngestResponse
from academic_ingest.classification.page_classifier import PageClassifier
from academic_ingest.db.models import CrawlJobModel
from academic_ingest.db.repositories import SourceRepository
from academic_ingest.extraction.fake_client import FakeStructuredExtractionClient
from academic_ingest.jobs.ingest_job import run_ingest_job
from academic_ingest.models.domain import EvidenceBackedRecord, SourcePage
from academic_ingest.models.enums import JobStatus
from academic_ingest.publishing.service import PublishingService

router = APIRouter(prefix="/pages", tags=["pages"])
SourceUrlForm = Annotated[str, Form()]
FixtureUpload = Annotated[UploadFile, File()]


@router.post("/ingest", response_model=PageIngestResponse)
async def ingest_page(
    request: Request,
    source_url: SourceUrlForm,
    file: FixtureUpload,
    session: SessionDep,
    config: InstitutionConfigDep,
) -> PageIngestResponse:
    if not config.is_allowed_url(source_url):
        raise HTTPException(status_code=422, detail="source URL is outside configured UW scope")
    maximum = config.request_policy.max_response_bytes
    raw = await file.read(maximum + 1)
    if len(raw) > maximum:
        raise HTTPException(status_code=413, detail="fixture exceeds configured response limit")
    if not raw:
        raise HTTPException(status_code=422, detail="fixture is empty")

    await ensure_institution(session, config)
    job = CrawlJobModel(
        id=uuid4(),
        institution_id=config.institution_id,
        started_at=datetime.now(UTC),
        status=JobStatus.RUNNING.value,
        configuration={"fixture_only": True, "source_url": source_url},
        parser_versions={},
        warnings=[],
        errors=[],
    )
    session.add(job)
    await session.commit()

    content_type = (file.content_type or "application/octet-stream").split(";", 1)[0]
    classified = PageClassifier().classify(source_url, raw, content_type=content_type)
    page = SourcePage(
        institution_id=config.institution_id,
        canonical_url=source_url,
        final_url=source_url,
        page_title=classified.title,
        source_type=classified.source_type,
        policy_family=classified.policy_family,
        campus=config.campus,
        http_status=200,
        content_type=content_type,
    )
    sources = SourceRepository(session)
    stored_page = await sources.upsert_page(page)
    snapshot = await sources.create_snapshot(
        stored_page.id,
        raw,
        job.id,
        response_headers={"content-type": content_type},
        parser_version="api-fixture-v1",
    )
    context = AdapterContext(
        page=classified,
        raw_content=raw,
        source_snapshot_id=snapshot.id,
        crawl_job_id=job.id,
        institution_id=config.institution_id,
        campus=config.campus,
        source_page_id=stored_page.id,
    )
    pipeline = await run_ingest_job(
        [context],
        extraction_client=FakeStructuredExtractionClient(),
        adapter_registry=request.app.state.adapter_registry,
    )
    candidates = [record for record in pipeline.records if isinstance(record, EvidenceBackedRecord)]
    publication = await PublishingService(
        session,
        snapshots={snapshot.id: raw},
    ).publish(candidates)

    stored_job = await session.get(CrawlJobModel, job.id)
    if stored_job is not None:
        stored_job.completed_at = datetime.now(UTC)
        stored_job.status = (
            JobStatus.PARTIAL.value
            if pipeline.errors or publication.rejected_record_ids
            else JobStatus.COMPLETED.value
        )
        stored_job.pages_discovered = 1
        stored_job.pages_fetched = 1
        stored_job.records_created = len(publication.published)
        stored_job.warnings = [
            f"{warning.code}: {warning.message}" for warning in pipeline.warnings
        ]
        stored_job.errors = [f"{error.code}: {error.message}" for error in pipeline.errors]
        await session.commit()

    return PageIngestResponse(
        source_page_id=str(stored_page.id),
        source_snapshot_id=str(snapshot.id),
        crawl_job_id=str(job.id),
        records_extracted=len(pipeline.records),
        records_published=len(publication.published),
        record_version_ids=[str(version.id) for version in publication.published],
        review_task_ids=[str(task.id) for task in publication.review_tasks],
        warnings=[warning.model_dump(mode="json") for warning in pipeline.warnings],
        errors=[error.model_dump(mode="json") for error in pipeline.errors],
    )
