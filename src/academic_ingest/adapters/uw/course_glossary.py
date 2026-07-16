from __future__ import annotations

from dataclasses import dataclass

from selectolax.parser import HTMLParser

from academic_ingest.adapters.base import AdapterContext, AdapterResult
from academic_ingest.classification.page_classifier import ClassifiedPage
from academic_ingest.models.domain import EvidenceRecord
from academic_ingest.models.enums import (
    AuthorityTier,
    ConfidenceTier,
    ReviewStatus,
)


@dataclass(frozen=True)
class GlossaryEntry:
    term: str
    definition: str
    evidence: EvidenceRecord


class CourseGlossaryAdapter:
    name = "uw.course_glossary"
    version = "1.0.0"

    def matches(self, page: ClassifiedPage) -> bool:
        return page.adapter_name == self.name

    def extract(self, context: AdapterContext) -> AdapterResult:
        tree = HTMLParser(context.raw_content)
        entries: list[GlossaryEntry] = []
        for heading in tree.css("h2, h3"):
            term = " ".join(heading.text(separator=" ", strip=True).split())
            sibling = heading.next
            definition_parts: list[str] = []
            while sibling is not None and sibling.tag not in {"h2", "h3"}:
                text = " ".join(sibling.text(separator=" ", strip=True).split())
                if text:
                    definition_parts.append(text)
                sibling = sibling.next
            definition = " ".join(definition_parts)
            if not term or not definition:
                continue
            heading_id = heading.attributes.get("id")
            evidence = EvidenceRecord(
                source_snapshot_id=context.source_snapshot_id,
                source_url=context.page.url,
                page_title=context.page.title,
                evidence_text=f"{term}\n{definition}",
                css_selector=f"#{heading_id}" if heading_id else None,
                heading_context=term,
                retrieved_at=context.retrieved_at,
                parser_name=self.name,
                parser_version=self.version,
                authority_tier=AuthorityTier.OFFICIAL_CATALOG,
                confidence_tier=ConfidenceTier.HIGH_CONFIDENCE,
                reviewer_status=ReviewStatus.NOT_REQUIRED,
            )
            entries.append(GlossaryEntry(term=term, definition=definition, evidence=evidence))
        return AdapterResult(records=entries)
