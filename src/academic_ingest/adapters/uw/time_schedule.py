from __future__ import annotations

from selectolax.parser import HTMLParser

from academic_ingest.adapters.base import AdapterContext, AdapterResult
from academic_ingest.classification.page_classifier import ClassifiedPage
from academic_ingest.discovery.link_discovery import discover_links
from academic_ingest.models.domain import PipelineIssue


class TimeScheduleAdapter:
    name = "uw.time_schedule"
    version = "1.0.0"

    def matches(self, page: ClassifiedPage) -> bool:
        return page.adapter_name == self.name

    def extract(self, context: AdapterContext) -> AdapterResult:
        tree = HTMLParser(context.raw_content)
        excluded_netid = any(
            "netid" in node.text(separator=" ", strip=True).lower()
            or "netid" in (node.attributes.get("href") or "").lower()
            for node in tree.css("a[href]")
        )
        links = discover_links(
            context.page.url,
            context.raw_content,
            allowed_domains={"www.washington.edu"},
        )
        public_schedule_links = [
            link for link in links if "/students/timeschd/" in link and "netid" not in link.lower()
        ]
        warnings = []
        if excluded_netid:
            warnings.append(
                PipelineIssue(
                    code="netid_schedule_excluded",
                    message="NetID-required Time Schedule links were not followed",
                    source_url=context.page.url,
                )
            )
        return AdapterResult(discovered_links=public_schedule_links, warnings=warnings)
