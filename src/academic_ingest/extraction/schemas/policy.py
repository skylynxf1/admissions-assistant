from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StructuredTable(BaseModel):
    model_config = ConfigDict(extra="forbid")

    heading: str | None = None
    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    def as_source_text(self) -> str:
        cells = [self.heading or "", *self.headers]
        cells.extend(cell for row in self.rows for cell in row)
        cells.extend(self.notes)
        return " ".join(cell for cell in cells if cell)


class ExtractionContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    institution_id: str
    institution_name: str
    campus: str
    canonical_url: str
    page_title: str
    policy_family: str
    catalog_or_effective_period_context: dict[str, Any] = Field(default_factory=dict)
    cleaned_source_text: str = ""
    structured_tables: list[StructuredTable] = Field(default_factory=list)
    relevant_dom_blocks: list[str] = Field(default_factory=list)
    known_deterministic_fields: dict[str, Any] = Field(default_factory=dict)

    def supplied_source_text(self) -> str:
        parts = [self.cleaned_source_text]
        parts.extend(table.as_source_text() for table in self.structured_tables)
        parts.extend(self.relevant_dom_blocks)
        return " ".join(part for part in parts if part)

    def bounded(self, max_source_chars: int) -> ExtractionContext:
        if max_source_chars <= 0:
            raise ValueError("max_source_chars must be positive")
        remaining = max_source_chars
        cleaned = self.cleaned_source_text[:remaining]
        remaining -= len(cleaned)
        dom_blocks: list[str] = []
        for block in self.relevant_dom_blocks:
            if remaining <= 0:
                break
            bounded_block = block[:remaining]
            dom_blocks.append(bounded_block)
            remaining -= len(bounded_block)
        return self.model_copy(
            update={"cleaned_source_text": cleaned, "relevant_dom_blocks": dom_blocks}
        )

    def request_json(self, max_source_chars: int) -> str:
        return json.dumps(
            self.bounded(max_source_chars).model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
        )


class ExtractionProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposed_fields: dict[str, Any] = Field(default_factory=dict)
    exact_evidence_strings: list[str] = Field(default_factory=list)
    unresolved_fields: list[str] = Field(default_factory=list)
    ambiguity_warnings: list[str] = Field(default_factory=list)
    possible_conflicts: list[str] = Field(default_factory=list)
    suggested_review_question: str | None = None
    source_urls: list[str] = Field(default_factory=list)


class ExtractionMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_id: str
    prompt_version: str
    schema_version: str
    request_id: str | None = None
    usage: dict[str, Any] = Field(default_factory=dict)
    validation_result: Literal["accepted", "rejected"]
    retry_count: int = Field(default=0, ge=0)


class ExtractionResult[ResultT: BaseModel](BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: ResultT | None
    metadata: ExtractionMetadata
    validation_issues: list[str] = Field(default_factory=list)


class ExtractionCall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: str
    context: ExtractionContext
