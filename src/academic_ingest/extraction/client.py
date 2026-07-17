from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from academic_ingest.extraction.schemas.policy import (
    ExtractionContext,
    ExtractionProposal,
    ExtractionResult,
)


class StructuredExtractionClient(Protocol):
    async def classify_page(
        self, context: ExtractionContext
    ) -> ExtractionResult[ExtractionProposal]: ...

    async def extract_course_requirement(
        self, context: ExtractionContext
    ) -> ExtractionResult[ExtractionProposal]: ...

    async def parse_requirement_expression(
        self, context: ExtractionContext
    ) -> ExtractionResult[ExtractionProposal]: ...

    async def extract_policy(
        self, context: ExtractionContext
    ) -> ExtractionResult[ExtractionProposal]: ...

    async def compare_sources(
        self, contexts: Sequence[ExtractionContext]
    ) -> ExtractionResult[ExtractionProposal]: ...

    async def summarize_unresolved_issue(
        self, context: ExtractionContext, issue: str
    ) -> ExtractionResult[ExtractionProposal]: ...
