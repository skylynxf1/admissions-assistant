from __future__ import annotations

from academic_ingest.adapters.base import AdapterContext, AdapterResult
from academic_ingest.classification.page_classifier import ClassifiedPage
from academic_ingest.discovery.link_discovery import discover_links
from academic_ingest.models.domain import PipelineIssue


class EquivalencyGuideAdapter:
    name = "uw.equivalency_guide"
    version = "1.0.0"

    def matches(self, page: ClassifiedPage) -> bool:
        return page.adapter_name == self.name

    def extract(self, context: AdapterContext) -> AdapterResult:
        links = discover_links(
            context.page.url,
            context.raw_content,
            allowed_domains={"admit.washington.edu"},
        )
        guide_links = [link for link in links if "/apply/transfer/equivalency-guide/" in link]
        return AdapterResult(
            discovered_links=guide_links,
            warnings=[
                PipelineIssue(
                    code="equivalency_snapshot_only",
                    message=(
                        "Equivalency Guide support is discovery and snapshot only; "
                        "no policy mapping was inferred"
                    ),
                    source_url=context.page.url,
                )
            ],
        )
