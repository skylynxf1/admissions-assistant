"""Deterministic validation gates for extracted academic records."""

from academic_ingest.validation.evidence import validate_candidate, validate_evidence
from academic_ingest.validation.models import ValidationIssue, ValidationReport

__all__ = ["ValidationIssue", "ValidationReport", "validate_candidate", "validate_evidence"]
