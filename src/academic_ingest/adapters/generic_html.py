from __future__ import annotations

from dataclasses import dataclass

from selectolax.parser import HTMLParser

from academic_ingest.adapters.base import AdapterContext, AdapterResult
from academic_ingest.classification.page_classifier import ClassifiedPage


@dataclass(frozen=True)
class EvidenceBlock:
    text: str
    css_selector: str
    heading_context: str | None = None
    page_number: int | None = None


class GenericHTMLAdapter:
    name = "generic_html"
    version = "1.0.0"

    def __init__(self, *, max_blocks: int = 100) -> None:
        self.max_blocks = max_blocks

    def matches(self, page: ClassifiedPage) -> bool:
        return page.adapter_name == self.name

    def extract(self, context: AdapterContext) -> AdapterResult:
        tree = HTMLParser(context.raw_content)
        blocks: list[EvidenceBlock] = []
        current_heading: str | None = None
        for index, node in enumerate(tree.css("h1, h2, h3, p, li, table")):
            if len(blocks) >= self.max_blocks:
                break
            text = " ".join(node.text(separator=" ", strip=True).split())
            if not text:
                continue
            if node.tag in {"h1", "h2", "h3"}:
                current_heading = text
                continue
            node_id = node.attributes.get("id")
            selector = f"#{node_id}" if node_id else f"{node.tag}:nth-of-type({index + 1})"
            blocks.append(
                EvidenceBlock(text=text, css_selector=selector, heading_context=current_heading)
            )
        return AdapterResult(records=blocks)
