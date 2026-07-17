from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from academic_ingest.api.dependencies import (
    InstitutionConfigDep,
    SessionDep,
    SettingsDep,
    ensure_institution,
)
from academic_ingest.api.schemas.common import CrawlJobCreate
from academic_ingest.api.serialization import serialize_model
from academic_ingest.db.models import CrawlJobModel
from academic_ingest.models.enums import JobStatus

router = APIRouter(prefix="/crawl-jobs", tags=["crawl jobs"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_crawl_job(
    request: CrawlJobCreate,
    session: SessionDep,
    config: InstitutionConfigDep,
    settings: SettingsDep,
) -> dict[str, object]:
    urls = request.urls or config.seed_urls
    invalid = [url for url in urls if not config.is_allowed_url(url)]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "source_outside_configured_scope", "urls": invalid},
        )
    await ensure_institution(session, config)
    warnings = []
    if request.allow_network and not settings.network_enabled:
        warnings.append("network_requested_but_disabled_by_server")
    job = CrawlJobModel(
        institution_id=config.institution_id,
        status=JobStatus.QUEUED.value,
        configuration={
            "urls": urls,
            "allow_network": request.allow_network and settings.network_enabled,
        },
        parser_versions={},
        warnings=warnings,
        errors=[],
    )
    session.add(job)
    await session.commit()
    return serialize_model(job)


@router.get("/{job_id}")
async def get_crawl_job(
    job_id: UUID,
    session: SessionDep,
) -> dict[str, object]:
    job = await session.get(CrawlJobModel, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="crawl job not found")
    return serialize_model(job)
