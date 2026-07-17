from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request

from app.graph import PrerequisiteCycleError
from app.models import RecommendationRequest, RecommendationResponse
from app.repository import (
    InMemoryRecommendationRepository,
    RecommendationRepository,
    ScenarioNotFoundError,
    SupabaseRecommendationRepository,
)
from app.sample_data import SCENARIO_ID, sample_dataset
from app.service import RecommendationService


def default_repository() -> RecommendationRepository:
    if os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_ROLE_KEY"):
        return SupabaseRecommendationRepository.from_env()
    return InMemoryRecommendationRepository({SCENARIO_ID: sample_dataset()})


def create_app(repository: RecommendationRepository | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.repository = repository or default_repository()
        yield

    api = FastAPI(
        title="Pathwise Course Recommendation Service",
        version="0.1.0",
        description=(
            "Deterministic prerequisite eligibility and ranked course recommendations. "
            "Language models may explain these outputs but do not calculate them."
        ),
        lifespan=lifespan,
    )

    @api.get("/health")
    async def health(request: Request) -> dict[str, str]:
        mode = "supabase" if isinstance(request.app.state.repository, SupabaseRecommendationRepository) else "sample"
        return {"status": "ok", "mode": mode}

    @api.post(
        "/api/v1/scenarios/{scenario_id}/recommendations",
        response_model=RecommendationResponse,
    )
    async def recommendations(
        scenario_id: str,
        body: RecommendationRequest,
        request: Request,
    ) -> RecommendationResponse:
        service = RecommendationService(request.app.state.repository)
        try:
            return await service.recommend(scenario_id, body)
        except ScenarioNotFoundError as error:
            raise HTTPException(status_code=404, detail="Planning scenario not found.") from error
        except PrerequisiteCycleError as error:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "PREREQUISITE_CYCLE",
                    "message": "Recommendation generation rejected cyclic prerequisite data.",
                    "cycles": error.cycles,
                },
            ) from error
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    return api


app = create_app()
