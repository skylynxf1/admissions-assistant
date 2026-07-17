from __future__ import annotations

from collections.abc import Sequence

from selectolax.parser import HTMLParser, Node

from academic_ingest.adapters.base import AdapterContext
from academic_ingest.adapters.registry import AdapterNotFoundError, AdapterRegistry
from academic_ingest.extraction.client import StructuredExtractionClient
from academic_ingest.extraction.schemas.policy import ExtractionContext, StructuredTable
from academic_ingest.models.domain import PipelineIssue, PipelineResult
from academic_ingest.models.enums import Severity


def _cleaned_text(raw_content: bytes) -> str:
    decoded = raw_content.decode("utf-8", errors="replace")
    tree = HTMLParser(decoded)
    if tree.root is None:
        return " ".join(decoded.split())
    return " ".join(tree.root.text(separator=" ", strip=True).split())


def _table(node: Node) -> StructuredTable:
    headers = [" ".join(cell.text(separator=" ", strip=True).split()) for cell in node.css("th")]
    rows: list[list[str]] = []
    for row in node.css("tr"):
        cells = [
            " ".join(cell.text(separator=" ", strip=True).split())
            for cell in row.css("td")
        ]
        if cells:
            rows.append(cells)
    return StructuredTable(headers=headers, rows=rows)


def build_extraction_context(context: AdapterContext) -> ExtractionContext:
    tree = HTMLParser(context.raw_content)
    tables = [_table(table) for table in tree.css("table")]
    dom_blocks = [
        " ".join(node.text(separator=" ", strip=True).split())
        for node in tree.css("h1,h2,h3,p,li")[:200]
        if node.text(strip=True)
    ]
    deterministic_fields: dict[str, object] = {
        "classified_source_type": context.page.source_type.value,
        "selected_adapter": context.page.adapter_name,
    }
    if context.selected_course_codes is not None:
        deterministic_fields["selected_course_codes"] = sorted(context.selected_course_codes)
    if context.selected_program_names is not None:
        deterministic_fields["selected_program_names"] = sorted(
            context.selected_program_names
        )
    return ExtractionContext(
        institution_id=context.institution_id,
        institution_name=(
            "University of Washington"
            if context.institution_id == "uw-seattle"
            else context.institution_id
        ),
        campus=context.campus,
        canonical_url=context.page.url,
        page_title=context.page.title,
        policy_family=context.page.policy_family.value,
        cleaned_source_text=_cleaned_text(context.raw_content),
        structured_tables=tables,
        relevant_dom_blocks=dom_blocks,
        known_deterministic_fields=deterministic_fields,
    )


async def run_ingest_job(
    inputs: Sequence[AdapterContext],
    *,
    extraction_client: StructuredExtractionClient,
    adapter_registry: AdapterRegistry,
) -> PipelineResult:
    result = PipelineResult()
    for context in inputs:
        result.parser_metrics.pages_attempted += 1
        try:
            try:
                adapter = adapter_registry.for_context(context)
            except AdapterNotFoundError:
                result.parser_metrics.gpt_fallback_calls += 1
                fallback = await extraction_client.extract_policy(
                    build_extraction_context(context)
                )
                if fallback.data is None:
                    result.parser_metrics.parse_failures += 1
                    result.errors.append(
                        PipelineIssue(
                            code="structured_fallback_rejected",
                            message="; ".join(fallback.validation_issues),
                            source_url=context.page.url,
                            severity=Severity.ERROR,
                        )
                    )
                    continue
                result.records.append(fallback.data)
                result.parser_metrics.records_extracted += 1
            else:
                adapter_result = adapter.extract(context)
                extracted = [*adapter_result.records, *adapter_result.requirements]
                result.records.extend(extracted)
                result.warnings.extend(adapter_result.warnings)
                result.review_tasks.extend(adapter_result.review_tasks)
                result.discovered_links.extend(adapter_result.discovered_links)
                result.parser_metrics.records_extracted += len(extracted)
            result.parser_metrics.parse_successes += 1
        except Exception as error:
            result.parser_metrics.parse_failures += 1
            result.errors.append(
                PipelineIssue(
                    code="page_ingest_failed",
                    message=f"{type(error).__name__}: {error}",
                    source_url=context.page.url,
                    severity=Severity.ERROR,
                )
            )
    return result

