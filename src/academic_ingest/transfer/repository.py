"""Read-side repository abstraction for published equivalency records."""

from __future__ import annotations

from typing import Protocol

from academic_ingest.transfer.models import EquivalencyRecord


class EquivalencyReadRepository(Protocol):
    """Read access to published equivalency records for a source/destination pair."""

    def records_for(
        self, source_institution_id: str, destination_institution_id: str
    ) -> list[EquivalencyRecord]:
        """Return every published equivalency record for the given institution pair."""
        ...


class InMemoryEquivalencyRepository:
    """An in-memory `EquivalencyReadRepository`, primarily for tests and defaults."""

    def __init__(self, records: dict[tuple[str, str], list[EquivalencyRecord]]) -> None:
        self._records = records

    def records_for(
        self, source_institution_id: str, destination_institution_id: str
    ) -> list[EquivalencyRecord]:
        return self._records.get((source_institution_id, destination_institution_id), [])
