"""Strict schemas shared by structured extraction implementations."""

from academic_ingest.extraction.schemas.policy import (
    ExtractionContext,
    ExtractionMetadata,
    ExtractionProposal,
    ExtractionResult,
    StructuredTable,
)

__all__ = [
    "ExtractionContext",
    "ExtractionMetadata",
    "ExtractionProposal",
    "ExtractionResult",
    "StructuredTable",
]
