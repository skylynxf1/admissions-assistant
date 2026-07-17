from __future__ import annotations

from collections.abc import Mapping, Sequence

from academic_ingest.extraction.prompts import PROMPT_VERSION, SCHEMA_VERSION
from academic_ingest.extraction.schemas.policy import (
    ExtractionCall,
    ExtractionContext,
    ExtractionMetadata,
    ExtractionProposal,
    ExtractionResult,
)
from academic_ingest.extraction.validation import validate_extraction_proposal


class FakeStructuredExtractionClient:
    def __init__(
        self,
        *,
        results: Mapping[str, ExtractionProposal | Exception] | None = None,
    ) -> None:
        self.results = dict(results or {})
        self.calls: list[ExtractionCall] = []

    async def _execute(
        self,
        operation: str,
        context: ExtractionContext,
    ) -> ExtractionResult[ExtractionProposal]:
        self.calls.append(ExtractionCall(operation=operation, context=context))
        configured = self.results.get(operation, ExtractionProposal())
        if isinstance(configured, Exception):
            raise configured
        issues = validate_extraction_proposal(context, configured)
        accepted = not issues
        return ExtractionResult[ExtractionProposal](
            data=configured if accepted else None,
            metadata=ExtractionMetadata(
                model_id="fake-structured-extraction",
                prompt_version=PROMPT_VERSION,
                schema_version=SCHEMA_VERSION,
                validation_result="accepted" if accepted else "rejected",
            ),
            validation_issues=issues,
        )

    async def classify_page(
        self, context: ExtractionContext
    ) -> ExtractionResult[ExtractionProposal]:
        return await self._execute("classify_page", context)

    async def extract_course_requirement(
        self, context: ExtractionContext
    ) -> ExtractionResult[ExtractionProposal]:
        return await self._execute("extract_course_requirement", context)

    async def parse_requirement_expression(
        self, context: ExtractionContext
    ) -> ExtractionResult[ExtractionProposal]:
        return await self._execute("parse_requirement_expression", context)

    async def extract_policy(
        self, context: ExtractionContext
    ) -> ExtractionResult[ExtractionProposal]:
        return await self._execute("extract_policy", context)

    async def compare_sources(
        self, contexts: Sequence[ExtractionContext]
    ) -> ExtractionResult[ExtractionProposal]:
        if not contexts:
            raise ValueError("at least one extraction context is required")
        combined = contexts[0].model_copy(
            update={
                "cleaned_source_text": "\n\n".join(
                    context.supplied_source_text() for context in contexts
                )
            }
        )
        return await self._execute("compare_sources", combined)

    async def summarize_unresolved_issue(
        self,
        context: ExtractionContext,
        issue: str,
    ) -> ExtractionResult[ExtractionProposal]:
        enriched = context.model_copy(
            update={
                "known_deterministic_fields": {
                    **context.known_deterministic_fields,
                    "unresolved_issue": issue,
                }
            }
        )
        return await self._execute("summarize_unresolved_issue", enriched)
