"""Pydantic models for the deterministic transfer-outcome resolver."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from academic_ingest.models.transfer_state import TransferState


class SourceCourseInput(BaseModel):
    """A single source-institution course to resolve a transfer outcome for."""

    code: str
    title: str | None = None


class EquivalencyRecord(BaseModel):
    """A single published source-to-destination equivalency mapping."""

    source_course_codes: list[str] = Field(min_length=1)
    mapping_type: str
    destination_outcome: str
    credits_awarded: float | None = None
    minimum_grade: str | None = None
    conditions: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)


class TransferOutcome(BaseModel):
    """The resolved transfer outcome for a single source course."""

    source_course: SourceCourseInput
    state: TransferState
    destination_outcomes: list[str] = Field(default_factory=list)
    credits_awarded: float | None = None
    minimum_grade: str | None = None
    conditions: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)
    detail: str | None = None
