from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from academic_ingest.api.dependencies import SessionDep
from academic_ingest.api.serialization import (
    evidence_for_version,
    list_current_versions,
    serialize_model,
    serialize_version,
)
from academic_ingest.db.models import RecordVersionModel, RequirementExpressionModel

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("")
async def list_courses(
    session: SessionDep,
    institution: str | None = None,
    campus: str | None = None,
    subject: str | None = None,
    number: str | None = None,
    effective_at: datetime | None = None,
) -> dict[str, object]:
    versions = await list_current_versions(
        session,
        "course",
        filters={
            "institution_id": institution,
            "campus": campus,
            "subject": subject,
            "number": number,
        },
        effective_at=effective_at,
    )
    return {"items": [serialize_version(version) for version in versions]}


@router.get("/{course_id}")
async def get_course(
    course_id: UUID,
    session: SessionDep,
) -> dict[str, object]:
    version = await session.get(RecordVersionModel, course_id)
    if version is None or version.record_type != "course":
        raise HTTPException(status_code=404, detail="course not found")
    versions = await session.scalars(
        select(RecordVersionModel)
        .where(
            RecordVersionModel.record_type == "course",
            RecordVersionModel.canonical_key == version.canonical_key,
        )
        .order_by(RecordVersionModel.version_number)
    )
    expression = None
    expression_id = version.payload.get("prerequisite_expression_id")
    if expression_id:
        stored_expression = await session.get(RequirementExpressionModel, UUID(expression_id))
        if stored_expression is not None:
            expression = serialize_model(stored_expression)
    return {
        **serialize_version(version),
        "evidence": await evidence_for_version(session, version),
        "versions": [serialize_version(item) for item in versions],
        "prerequisite_ast": expression,
    }
