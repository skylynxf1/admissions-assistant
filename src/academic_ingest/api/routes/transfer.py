"""Transfer-outcome API: resolves synthetic/published equivalency records into
the canonical 9-state TransferState vocabulary for a given pathway."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from academic_ingest.pathways.registry import UnknownPathwayError, get_pathway, load_pathways
from academic_ingest.transfer.curated_equivalencies import curated_records
from academic_ingest.transfer.models import SourceCourseInput, TransferOutcome
from academic_ingest.transfer.repository import (
    EquivalencyReadRepository,
    InMemoryEquivalencyRepository,
)
from academic_ingest.transfer.resolver import resolve_outcomes

router = APIRouter(prefix="/transfer", tags=["transfer"])


class TransferOutcomeRequest(BaseModel):
    pathway_key: str
    courses: list[SourceCourseInput]


class TransferOutcomeResponse(BaseModel):
    pathway_key: str
    source_institution_id: str
    destination_institution_id: str
    outcomes: list[TransferOutcome]


def get_equivalency_repository() -> EquivalencyReadRepository:
    """Default equivalency repository dependency.

    Returns an in-memory repository built from `curated_records()` — the hand-
    verified, cited published equivalency data in
    `academic_ingest.transfer.curated_equivalencies` (see
    docs/equivalencies/SOURCES.md). Tests override this via
    `app.dependency_overrides`.
    """
    return InMemoryEquivalencyRepository(curated_records())


EquivalencyRepositoryDep = Annotated[EquivalencyReadRepository, Depends(get_equivalency_repository)]


@router.post("/outcomes")
async def get_transfer_outcomes(
    request: TransferOutcomeRequest,
    repo: EquivalencyRepositoryDep,
) -> TransferOutcomeResponse:
    pathways = load_pathways()
    try:
        pathway = get_pathway(request.pathway_key, pathways)
        outcomes = resolve_outcomes(request.pathway_key, request.courses, repo, pathways)
    except UnknownPathwayError as exc:
        raise HTTPException(
            status_code=404, detail=f"Unknown pathway: {request.pathway_key}"
        ) from exc
    return TransferOutcomeResponse(
        pathway_key=request.pathway_key,
        source_institution_id=pathway.source_institution_id,
        destination_institution_id=pathway.destination_institution_id,
        outcomes=outcomes,
    )
