from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from academic_ingest.models.enums import Severity

ValidationDisposition = Literal["allow", "review", "block_publish"]


class ValidationIssue(BaseModel):
    code: str
    message: str
    severity: Severity
    disposition: ValidationDisposition
    evidence_id: UUID | None = None
    field: str | None = None


class ValidationReport(BaseModel):
    accepted: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
