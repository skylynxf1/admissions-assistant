from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

from selectolax.parser import HTMLParser

from academic_ingest.classification.rules import UW_CLASSIFICATION_RULES
from academic_ingest.models.enums import PolicyFamily, SourceType


@dataclass(frozen=True)
class ClassifiedPage:
    url: str
    title: str
    content_type: str
    source_type: SourceType
    policy_family: PolicyFamily
    adapter_name: str


class PageClassifier:
    def classify(self, url: str, raw: bytes, *, content_type: str) -> ClassifiedPage:
        media_type = content_type.split(";", 1)[0].strip().lower()
        if media_type == "application/pdf" or urlsplit(url).path.lower().endswith(".pdf"):
            return ClassifiedPage(
                url=url,
                title="PDF policy document",
                content_type=media_type,
                source_type=SourceType.PDF,
                policy_family=PolicyFamily.ADMISSIONS,
                adapter_name="pdf_policy",
            )
        tree = HTMLParser(raw)
        title_node = tree.css_first("title") or tree.css_first("h1")
        title = title_node.text(strip=True) if title_node is not None else "Untitled source page"
        path = urlsplit(url).path
        for rule in UW_CLASSIFICATION_RULES:
            if rule.path_pattern.fullmatch(path):
                return ClassifiedPage(
                    url=url,
                    title=title,
                    content_type=media_type,
                    source_type=rule.source_type,
                    policy_family=rule.policy_family,
                    adapter_name=rule.adapter_name,
                )
        return ClassifiedPage(
            url=url,
            title=title,
            content_type=media_type,
            source_type=SourceType.GENERIC_HTML,
            policy_family=PolicyFamily.ADMISSIONS,
            adapter_name="generic_html",
        )
