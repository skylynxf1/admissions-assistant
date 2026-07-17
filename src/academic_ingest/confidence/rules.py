from __future__ import annotations

from pydantic import BaseModel, Field

from academic_ingest.models.enums import ConfidenceTier


class ConfidenceFactors(BaseModel):
    official_source: bool = False
    exact_evidence: bool = False
    deterministic_parser: bool = False
    schema_valid: bool = False
    current_or_dated: bool = False
    corroborated: bool = False
    ambiguous: bool = False
    unresolved_field_count: int = Field(default=0, ge=0)
    conflict_count: int = Field(default=0, ge=0)
    material_change: bool = False


class ConfidenceDecision(BaseModel):
    score: float = Field(ge=0, le=1)
    tier: ConfidenceTier
    publishable: bool
    requires_review: bool
    factor_explanations: dict[str, str]
    blocking_reasons: list[str] = Field(default_factory=list)
