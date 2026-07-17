from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader

from academic_ingest.adapters.base import AdapterContext, AdapterResult
from academic_ingest.adapters.generic_html import EvidenceBlock
from academic_ingest.classification.page_classifier import ClassifiedPage
from academic_ingest.models.domain import PipelineIssue


class PDFPolicyAdapter:
    name = "pdf_policy"
    version = "1.0.0"

    def __init__(self, *, max_pages: int = 200) -> None:
        self.max_pages = max_pages

    def matches(self, page: ClassifiedPage) -> bool:
        return page.adapter_name == self.name

    def extract(self, context: AdapterContext) -> AdapterResult:
        reader = PdfReader(BytesIO(context.raw_content), strict=True)
        if len(reader.pages) > self.max_pages:
            return AdapterResult(
                warnings=[
                    PipelineIssue(
                        code="pdf_page_limit_exceeded",
                        message=f"PDF has {len(reader.pages)} pages; limit is {self.max_pages}",
                        source_url=context.page.url,
                    )
                ]
            )
        blocks: list[EvidenceBlock] = []
        for index, page in enumerate(reader.pages, start=1):
            text = " ".join((page.extract_text() or "").split())
            if text:
                blocks.append(
                    EvidenceBlock(
                        text=text,
                        css_selector=f"pdf:page({index})",
                        page_number=index,
                    )
                )
        return AdapterResult(records=blocks)
