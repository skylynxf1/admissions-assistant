"""Dependency-injected structured extraction clients."""

from academic_ingest.extraction.client import StructuredExtractionClient
from academic_ingest.extraction.fake_client import FakeStructuredExtractionClient

__all__ = ["FakeStructuredExtractionClient", "StructuredExtractionClient"]
