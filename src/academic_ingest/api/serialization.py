from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from academic_ingest.db.models import EvidenceRecordModel, RecordVersionModel


def serialize_model(model: Any) -> dict[str, Any]:
    values = {column.name: getattr(model, column.name) for column in model.__table__.columns}
    encoded: dict[str, Any] = jsonable_encoder(values)
    return encoded


def serialize_version(version: RecordVersionModel) -> dict[str, Any]:
    return {
        "id": str(version.id),
        "record_type": version.record_type,
        "canonical_key": version.canonical_key,
        "version_number": version.version_number,
        "superseded": version.superseded,
        "effective_from": jsonable_encoder(version.effective_from),
        "effective_to": jsonable_encoder(version.effective_to),
        "created_at": jsonable_encoder(version.created_at),
        **version.payload,
    }


def _matches(value: Any, expected: str) -> bool:
    return str(value).casefold() == expected.casefold()


def _is_effective(payload: dict[str, Any], effective_at: datetime | None) -> bool:
    if effective_at is None:
        return True
    start = payload.get("effective_from")
    end = payload.get("effective_to")
    if start is not None and datetime.fromisoformat(str(start)) > effective_at:
        return False
    return not (end is not None and datetime.fromisoformat(str(end)) < effective_at)


async def list_current_versions(
    session: AsyncSession,
    record_type: str,
    *,
    filters: dict[str, str | None] | None = None,
    effective_at: datetime | None = None,
) -> list[RecordVersionModel]:
    result = await session.scalars(
        select(RecordVersionModel)
        .where(
            RecordVersionModel.record_type == record_type,
            RecordVersionModel.superseded.is_(False),
        )
        .order_by(RecordVersionModel.canonical_key)
    )
    versions = list(result)
    for field, expected in (filters or {}).items():
        if expected is not None:
            versions = [
                version for version in versions if _matches(version.payload.get(field), expected)
            ]
    return [version for version in versions if _is_effective(version.payload, effective_at)]


async def evidence_for_version(
    session: AsyncSession,
    version: RecordVersionModel,
) -> list[dict[str, Any]]:
    evidence_ids = [UUID(value) for value in version.evidence_record_ids]
    if not evidence_ids:
        return []
    result = await session.scalars(
        select(EvidenceRecordModel).where(EvidenceRecordModel.id.in_(evidence_ids))
    )
    by_id = {item.id: item for item in result}
    return [serialize_model(by_id[item_id]) for item_id in evidence_ids if item_id in by_id]
