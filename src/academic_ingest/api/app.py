from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from academic_ingest.adapters.generic_html import GenericHTMLAdapter
from academic_ingest.adapters.pdf_policy import PDFPolicyAdapter
from academic_ingest.adapters.registry import AdapterRegistry
from academic_ingest.adapters.uw.ap_credit import APCreditAdapter
from academic_ingest.adapters.uw.course_catalog import CourseCatalogAdapter
from academic_ingest.adapters.uw.course_glossary import CourseGlossaryAdapter
from academic_ingest.adapters.uw.equivalency_guide import EquivalencyGuideAdapter
from academic_ingest.adapters.uw.major_detail import MajorDetailAdapter
from academic_ingest.adapters.uw.majors_index import MajorsIndexAdapter
from academic_ingest.adapters.uw.time_schedule import TimeScheduleAdapter
from academic_ingest.adapters.uw.transfer_admissions import TransferAdmissionsAdapter
from academic_ingest.adapters.uw.transfer_policies import TransferPolicyAdapter
from academic_ingest.api.dependencies import SessionDep
from academic_ingest.api.routes import (
    conflicts,
    courses,
    crawl_jobs,
    pages,
    policies,
    programs,
    review_tasks,
    sources,
)
from academic_ingest.config.settings import Settings, load_institution_config
from academic_ingest.db.base import Base
from academic_ingest.db.session import create_engine_and_session


def build_default_adapter_registry() -> AdapterRegistry:
    return AdapterRegistry(
        [
            CourseCatalogAdapter(),
            CourseGlossaryAdapter(),
            MajorsIndexAdapter(),
            MajorDetailAdapter(),
            TransferAdmissionsAdapter(),
            TransferPolicyAdapter(),
            APCreditAdapter(),
            TimeScheduleAdapter(),
            EquivalencyGuideAdapter(),
            PDFPolicyAdapter(),
            GenericHTMLAdapter(),
        ]
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings()
    engine, session_factory = create_engine_and_session(resolved_settings.database_url)
    institution_config = load_institution_config(resolved_settings.institution_config_path)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if resolved_settings.database_url.startswith("sqlite+"):
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)
        yield
        await engine.dispose()

    app = FastAPI(title="Academic Ingestion API", version="0.1.0", lifespan=lifespan)
    app.state.settings = resolved_settings
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.institution_config = institution_config
    app.state.adapter_registry = build_default_adapter_registry()

    @app.get("/health")
    async def health(session: SessionDep) -> dict[str, object]:
        await session.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "database": "ok",
            "network_enabled": resolved_settings.network_enabled,
        }

    app.include_router(crawl_jobs.router)
    app.include_router(pages.router)
    app.include_router(sources.router)
    app.include_router(courses.router)
    app.include_router(programs.router)
    app.include_router(policies.router)
    app.include_router(conflicts.router)
    app.include_router(review_tasks.router)
    return app
