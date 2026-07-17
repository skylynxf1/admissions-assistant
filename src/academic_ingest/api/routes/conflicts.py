from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from academic_ingest.api.dependencies import SessionDep
from academic_ingest.api.serialization import serialize_model
from academic_ingest.db.models import ConflictRecordModel

router = APIRouter(prefix="/conflicts", tags=["conflicts"])


@router.get("")
async def list_conflicts(
    session: SessionDep,
    status: str | None = None,
    record_type: str | None = None,
) -> dict[str, object]:
    query = select(ConflictRecordModel)
    if status is not None:
        query = query.where(ConflictRecordModel.status == status)
    if record_type is not None:
        query = query.where(ConflictRecordModel.record_type == record_type)
    conflicts = await session.scalars(query.order_by(ConflictRecordModel.detected_at.desc()))
    return {"items": [serialize_model(conflict) for conflict in conflicts]}
