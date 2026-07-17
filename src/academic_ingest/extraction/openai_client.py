from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from openai import AsyncOpenAI

from academic_ingest.extraction.prompts import (
    PROMPT_VERSION,
    SCHEMA_VERSION,
    instructions_for,
)
from academic_ingest.extraction.schemas.policy import (
    ExtractionContext,
    ExtractionMetadata,
    ExtractionProposal,
    ExtractionResult,
)
from academic_ingest.extraction.validation import validate_extraction_proposal


class OpenAIStructuredExtractionClient:
    def __init__(
        self,
        *,
        client: Any | None = None,
        model: str = "gpt-5.6",
        max_source_chars: int = 100_000,
    ) -> None:
        if max_source_chars <= 0:
            raise ValueError("max_source_chars must be positive")
        self.client: Any = client if client is not None else AsyncOpenAI()
        self.model = model
        self.max_source_chars = max_source_chars

    async def _execute(
        self,
        operation: str,
        context: ExtractionContext,
    ) -> ExtractionResult[ExtractionProposal]:
        response = await self.client.responses.parse(
            model=self.model,
            instructions=instructions_for(operation),
            input=context.request_json(self.max_source_chars),
            text_format=ExtractionProposal,
            metadata={
                "prompt_version": PROMPT_VERSION,
                "schema_version": SCHEMA_VERSION,
                "operation": operation,
            },
            store=False,
        )
        parsed = response.output_parsed
        if parsed is None:
            issues = ["structured_output_missing_or_refused"]
            proposal = None
        else:
            proposal = (
                parsed
                if isinstance(parsed, ExtractionProposal)
                else ExtractionProposal.model_validate(parsed)
            )
            issues = validate_extraction_proposal(context, proposal)
        usage_object = getattr(response, "usage", None)
        usage = usage_object.model_dump(mode="json") if usage_object is not None else {}
        accepted = proposal is not None and not issues
        return ExtractionResult[ExtractionProposal](
            data=proposal if accepted else None,
            metadata=ExtractionMetadata(
                model_id=self.model,
                prompt_version=PROMPT_VERSION,
                schema_version=SCHEMA_VERSION,
                request_id=getattr(response, "id", None),
                usage=usage,
                validation_result="accepted" if accepted else "rejected",
                retry_count=0,
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

