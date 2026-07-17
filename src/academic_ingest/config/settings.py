from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from academic_ingest.models.enums import CalendarSystem, PolicyFamily


class RequestPolicy(BaseModel):
    user_agent: str
    requests_per_second: float = Field(gt=0, le=2)
    max_concurrency: int = Field(gt=0, le=4)
    timeout_seconds: float = Field(gt=0, le=120)
    retries: int = Field(ge=0, le=5)
    exponential_backoff: bool = True
    respect_robots_txt: bool = True
    max_response_bytes: int = Field(default=10 * 1024 * 1024, gt=0, le=50 * 1024 * 1024)

    @field_validator("user_agent")
    @classmethod
    def user_agent_has_contact_slot(cls, value: str) -> str:
        if "{contact_email}" not in value:
            raise ValueError("user_agent must contain {contact_email}")
        return value

    def build_user_agent(self, contact_email: str) -> str:
        if not contact_email.strip():
            raise ValueError("contact email is required for live network requests")
        return self.user_agent.format(contact_email=contact_email.strip())


class InstitutionConfig(BaseModel):
    institution_id: str
    legal_name: str
    common_name: str
    campus: str
    state: str
    country: str
    calendar_system: CalendarSystem
    allowed_domains: list[str]
    disallowed_campus_patterns: list[str]
    seed_urls: list[str]
    enabled_policy_families: list[PolicyFamily]
    request_policy: RequestPolicy

    @field_validator("allowed_domains", "disallowed_campus_patterns")
    @classmethod
    def lowercase_values(cls, values: list[str]) -> list[str]:
        return [value.lower().strip() for value in values]

    @model_validator(mode="after")
    def validate_seeds(self) -> InstitutionConfig:
        invalid = [url for url in self.seed_urls if not self.is_allowed_url(url)]
        if invalid:
            raise ValueError(f"seed URLs must be allowed Seattle HTTPS URLs: {invalid}")
        return self

    def url_belongs_to_disallowed_campus(self, url: str) -> bool:
        normalized = url.lower()
        return any(pattern in normalized for pattern in self.disallowed_campus_patterns)

    def is_allowed_url(self, url: str) -> bool:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower()
        return (
            parsed.scheme == "https"
            and host in set(self.allowed_domains)
            and not self.url_belongs_to_disallowed_campus(url)
        )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ACADEMIC_INGEST_", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///:memory:"
    contact_email: str = ""
    network_enabled: bool = False
    snapshot_root: Path = Path("var/snapshots")
    institution_config_path: Path = Path("config/institutions/uw_seattle.yaml")

    @model_validator(mode="after")
    def require_contact_for_network(self) -> Settings:
        if self.network_enabled and not self.contact_email.strip():
            raise ValueError("ACADEMIC_INGEST_CONTACT_EMAIL is required when network is enabled")
        return self


def load_institution_config(path: Path | str) -> InstitutionConfig:
    config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"institution configuration must be a mapping: {config_path}")
    return InstitutionConfig.model_validate(raw)
