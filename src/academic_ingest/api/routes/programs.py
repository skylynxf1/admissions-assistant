from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from academic_ingest.api.dependencies import SessionDep
from academic_ingest.api.serialization import (
    evidence_for_version,
    list_current_versions,
    serialize_version,
)
from academic_ingest.db.models import RecordVersionModel

router = APIRouter(prefix="/programs", tags=["programs"])


@router.get("")
async def list_programs(
    session: SessionDep,
    major_type: str | None = None,
    college_or_school: str | None = None,
) -> dict[str, object]:
    versions = await list_current_versions(
        session,
        "program",
        filters={"major_type": major_type, "college_or_school": college_or_school},
    )
    return {"items": [serialize_version(version) for version in versions]}


@router.get("/{program_id}")
async def get_program(
    program_id: UUID,
    session: SessionDep,
) -> dict[str, object]:
    version = await session.get(RecordVersionModel, program_id)
    if version is None or version.record_type != "program":
        raise HTTPException(status_code=404, detail="program not found")
    versions = await session.scalars(
        select(RecordVersionModel)
        .where(
            RecordVersionModel.record_type == "program",
            RecordVersionModel.canonical_key == version.canonical_key,
        )
        .order_by(RecordVersionModel.version_number)
    )
    requirements = await list_current_versions(session, "requirement")
    return {
        **serialize_version(version),
        "evidence": await evidence_for_version(session, version),
        "versions": [serialize_version(item) for item in versions],
        "requirements": [serialize_version(item) for item in requirements],
        "conflicts": [],
    }
