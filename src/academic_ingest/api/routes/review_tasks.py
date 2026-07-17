from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from academic_ingest.api.dependencies import SessionDep
from academic_ingest.api.schemas.common import ReviewResolutionRequest
from academic_ingest.api.serialization import serialize_model
from academic_ingest.db.models import ReviewTaskModel

router = APIRouter(prefix="/review-tasks", tags=["review tasks"])


@router.get("")
async def list_review_tasks(
    session: SessionDep,
    status: str | None = None,
    reason: str | None = None,
    severity: str | None = None,
) -> dict[str, object]:
    query = select(ReviewTaskModel)
    if status is not None:
        query = query.where(ReviewTaskModel.status == status)
    if reason is not None:
        query = query.where(ReviewTaskModel.reason == reason)
    if severity is not None:
        query = query.where(ReviewTaskModel.severity == severity)
    tasks = await session.scalars(query.order_by(ReviewTaskModel.created_at.desc()))
    return {"items": [serialize_model(task) for task in tasks]}


@router.post("/{review_task_id}/resolve")
async def resolve_review_task(
    review_task_id: UUID,
    request: ReviewResolutionRequest,
    session: SessionDep,
) -> dict[str, object]:
    task = await session.get(ReviewTaskModel, review_task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="review task not found")
    resolved_at = datetime.now(UTC)
    task.status = request.status
    task.resolved_at = resolved_at
    task.resolution = {
        "reviewer": request.reviewer,
        "status": request.status,
        "rationale": request.rationale,
        "resolved_at": resolved_at.isoformat(),
    }
    await session.commit()
    return serialize_model(task)
