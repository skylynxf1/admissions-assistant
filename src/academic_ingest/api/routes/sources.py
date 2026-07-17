from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from academic_ingest.api.dependencies import SessionDep
from academic_ingest.api.serialization import serialize_model
from academic_ingest.db.models import SourcePageModel, SourceSnapshotModel

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("")
async def list_sources(session: SessionDep) -> dict[str, object]:
    pages = await session.scalars(
        select(SourcePageModel).order_by(SourcePageModel.canonical_url)
    )
    return {"items": [serialize_model(page) for page in pages]}


@router.get("/{source_id}")
async def get_source(
    source_id: UUID,
    session: SessionDep,
) -> dict[str, object]:
    page = await session.get(SourcePageModel, source_id)
    if page is None:
        raise HTTPException(status_code=404, detail="source not found")
    snapshots = await session.scalars(
        select(SourceSnapshotModel)
        .where(SourceSnapshotModel.source_page_id == source_id)
        .order_by(SourceSnapshotModel.retrieved_at, SourceSnapshotModel.id)
    )
    return {**serialize_model(page), "snapshots": [serialize_model(item) for item in snapshots]}
