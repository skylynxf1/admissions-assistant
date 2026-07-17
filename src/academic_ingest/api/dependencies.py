from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from academic_ingest.config.settings import InstitutionConfig, Settings
from academic_ingest.db.models import InstitutionModel


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        yield session


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_institution_config(request: Request) -> InstitutionConfig:
    config: InstitutionConfig = request.app.state.institution_config
    return config


SessionDep = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
InstitutionConfigDep = Annotated[InstitutionConfig, Depends(get_institution_config)]


async def ensure_institution(
    session: AsyncSession,
    config: InstitutionConfig,
) -> InstitutionModel:
    institution = await session.get(InstitutionModel, config.institution_id)
    if institution is None:
        institution = InstitutionModel(
            id=config.institution_id,
            legal_name=config.legal_name,
            common_name=config.common_name,
            campus=config.campus,
            state=config.state,
            country=config.country,
            calendar_system=config.calendar_system.value,
            official_domains=config.allowed_domains,
        )
        session.add(institution)
        await session.commit()
    return institution
