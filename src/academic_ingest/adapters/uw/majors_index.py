from __future__ import annotations

from urllib.parse import urljoin, urlsplit

from selectolax.parser import HTMLParser, Node

from academic_ingest.adapters.base import AdapterContext, AdapterResult
from academic_ingest.classification.page_classifier import ClassifiedPage
from academic_ingest.discovery.link_discovery import canonicalize_url
from academic_ingest.models.domain import EvidenceRecord, PipelineIssue, Program
from academic_ingest.models.enums import (
    AuthorityTier,
    ConfidenceTier,
    MajorType,
    ReviewStatus,
)

MAJOR_TYPE_LABELS = {
    "capacity-constrained": MajorType.CAPACITY_CONSTRAINED,
    "minimum requirements": MajorType.MINIMUM_REQUIREMENTS,
    "open": MajorType.OPEN,
}


def _clean_text(node: Node) -> str:
    return " ".join(node.text(separator=" ", strip=True).split())


def _major_type(text: str) -> MajorType:
    lowered = text.lower()
    for label, major_type in MAJOR_TYPE_LABELS.items():
        if f"major type: {label}" in lowered:
            return major_type
    return MajorType.UNKNOWN


class MajorsIndexAdapter:
    name = "uw.majors_index"
    version = "1.0.0"

    def matches(self, page: ClassifiedPage) -> bool:
        return page.adapter_name == self.name

    def _cards(self, tree: HTMLParser) -> list[Node]:
        cards = tree.css("article.major-card, [data-major]")
        if cards:
            return cards
        fallback: list[Node] = []
        seen: set[int] = set()
        for anchor in tree.css('a[href*="/majors/"]'):
            candidate = anchor.parent.parent if anchor.parent is not None else None
            if candidate is not None and candidate.mem_id not in seen:  # type: ignore[comparison-overlap]
                fallback.append(candidate)
                seen.add(candidate.mem_id)  # type: ignore[arg-type]
        return fallback

    def extract(self, context: AdapterContext) -> AdapterResult:
        tree = HTMLParser(context.raw_content)
        result = AdapterResult()
        for card in self._cards(tree):
            link = card.css_first('a[href*="/majors/"]')
            if link is None:
                continue
            name = _clean_text(link)
            if not name or (
                context.selected_program_names is not None
                and name not in context.selected_program_names
            ):
                continue
            detail_url = canonicalize_url(urljoin(context.page.url, link.attributes["href"]), None)
            if urlsplit(detail_url).hostname != "admit.washington.edu":
                result.warnings.append(
                    PipelineIssue(
                        code="major_detail_host_rejected",
                        message=f"Major detail link is outside the Admissions host: {detail_url}",
                        source_url=context.page.url,
                    )
                )
                continue
            evidence_text = _clean_text(card)
            card_id = card.attributes.get("id")
            evidence = EvidenceRecord(
                source_snapshot_id=context.source_snapshot_id,
                source_url=context.page.url,
                page_title=context.page.title,
                evidence_text=evidence_text,
                css_selector=f"#{card_id}" if card_id else None,
                heading_context=name,
                retrieved_at=context.retrieved_at,
                parser_name=self.name,
                parser_version=self.version,
                authority_tier=AuthorityTier.OFFICIAL_ADMISSIONS,
                confidence_tier=ConfidenceTier.HIGH_CONFIDENCE,
                reviewer_status=ReviewStatus.NOT_REQUIRED,
            )
            result.records.append(
                Program(
                    institution_id=context.institution_id,
                    campus=context.campus,
                    evidence=[evidence],
                    parser_name=self.name,
                    parser_version=self.version,
                    crawl_job_id=context.crawl_job_id,
                    authority_tier=AuthorityTier.OFFICIAL_ADMISSIONS,
                    confidence_tier=ConfidenceTier.HIGH_CONFIDENCE,
                    review_status=ReviewStatus.NOT_REQUIRED,
                    official_name=name,
                    major_type=_major_type(evidence_text),
                    capacity_status=evidence_text,
                    source_scope="UW Admissions majors index summary",
                )
            )
            result.discovered_links.append(detail_url)
        result.discovered_links = sorted(set(result.discovered_links))
        return result
