from __future__ import annotations

from fastapi import APIRouter

from academic_ingest.api.dependencies import SessionDep
from academic_ingest.api.serialization import list_current_versions, serialize_version

router = APIRouter(tags=["policies"])


@router.get("/admissions-rules")
async def list_admissions_rules(
    session: SessionDep,
    applicant_type: str | None = None,
    rule_type: str | None = None,
) -> dict[str, object]:
    versions = await list_current_versions(
        session,
        "admissions_rule",
        filters={"applicant_type": applicant_type, "rule_type": rule_type},
    )
    return {"items": [serialize_version(version) for version in versions]}


@router.get("/transfer-policies")
async def list_transfer_policies(
    session: SessionDep,
    policy_type: str | None = None,
    applicant_type: str | None = None,
) -> dict[str, object]:
    versions = await list_current_versions(
        session,
        "transfer_policy",
        filters={"policy_type": policy_type, "applicant_type": applicant_type},
    )
    return {"items": [serialize_version(version) for version in versions]}


@router.get("/exam-credit")
async def list_exam_credit(
    session: SessionDep,
    exam_type: str | None = None,
    exam_name: str | None = None,
    score: float | None = None,
) -> dict[str, object]:
    versions = await list_current_versions(
        session,
        "exam_credit_rule",
        filters={"exam_type": exam_type, "exam_name": exam_name},
    )
    if score is not None:
        versions = [
            version
            for version in versions
            if float(version.payload["score_min"]) <= score <= float(version.payload["score_max"])
        ]
    return {"items": [serialize_version(version) for version in versions]}
