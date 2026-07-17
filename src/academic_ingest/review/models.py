from __future__ import annotations

from pydantic import BaseModel

from academic_ingest.confidence.rules import ConfidenceDecision
from academic_ingest.validation.models import ValidationReport


class ReviewContext(BaseModel):
    validation: ValidationReport
    confidence: ConfidenceDecision
    material_change: bool = False
