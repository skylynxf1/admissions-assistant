from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID

from academic_ingest.classification.page_classifier import ClassifiedPage
from academic_ingest.models.domain import PipelineIssue, ReviewTask


@dataclass(frozen=True)
class AdapterContext:
    page: ClassifiedPage
    raw_content: bytes
    source_snapshot_id: UUID
    crawl_job_id: UUID
    institution_id: str
    campus: str
    source_page_id: UUID | None = None
    retrieved_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    selected_course_codes: set[str] | None = None
    selected_program_names: set[str] | None = None


@dataclass
class AdapterResult:
    records: list[Any] = field(default_factory=list)
    requirements: list[Any] = field(default_factory=list)
    outcome_statistics: list[Any] = field(default_factory=list)
    conflict_candidates: list[Any] = field(default_factory=list)
    discovered_links: list[str] = field(default_factory=list)
    warnings: list[PipelineIssue] = field(default_factory=list)
    review_tasks: list[ReviewTask] = field(default_factory=list)


class SourceAdapter(Protocol):
    name: str
    version: str

    def matches(self, page: ClassifiedPage) -> bool: ...

    def extract(self, context: AdapterContext) -> AdapterResult: ...
