from collections import defaultdict
from pathlib import Path
from typing import Any

import docling
from docling.document_converter import DocumentConverter

from app.models import ParsedBlock, ParsedDocument, ParsedPage
from app.parsers.base import TranscriptParser


def _block_type(item: Any) -> str:
    name = item.__class__.__name__.lower()
    if "table" in name:
        return "table"
    if "title" in name or "heading" in name or "section" in name:
        return "heading"
    if getattr(item, "text", None):
        return "text"
    return "other"


def _bbox(provenance: Any) -> tuple[float, float, float, float] | None:
    box = getattr(provenance, "bbox", None)
    if box is None:
        return None
    values = [getattr(box, name, None) for name in ("l", "t", "r", "b")]
    if any(value is None for value in values):
        return None
    return tuple(float(value) for value in values)  # type: ignore[return-value]


class DoclingTranscriptParser(TranscriptParser):
    def __init__(self) -> None:
        self.converter = DocumentConverter()

    def parse(self, path: Path) -> ParsedDocument:
        result = self.converter.convert(path)
        document = result.document
        markdown = document.export_to_markdown()
        page_blocks: dict[int, list[ParsedBlock]] = defaultdict(list)

        for index, (item, _) in enumerate(document.iterate_items()):
            text = str(getattr(item, "text", "") or "").strip()
            if not text and hasattr(item, "export_to_markdown"):
                text = str(item.export_to_markdown()).strip()
            for provenance in list(getattr(item, "prov", []) or []):
                page_number = int(getattr(provenance, "page_no", 1))
                page_blocks[page_number].append(
                    ParsedBlock(
                        id=f"docling-{index}-{page_number}",
                        pageNumber=page_number,
                        type=_block_type(item),
                        text=text,
                        boundingBox=_bbox(provenance),
                    )
                )

        declared_pages = len(getattr(document, "pages", {}) or {})
        page_count = max([declared_pages, *page_blocks.keys()], default=0)
        if page_count < 1 or not markdown.strip():
            raise ValueError("Docling returned no readable transcript content.")

        pages: list[ParsedPage] = []
        for page_number in range(1, page_count + 1):
            blocks = page_blocks.get(page_number, [])
            text = "\n".join(block.text for block in blocks if block.text)
            pages.append(ParsedPage(pageNumber=page_number, markdown=text, text=text, blocks=blocks))

        return ParsedDocument(
            parser="docling",
            parserVersion=getattr(docling, "__version__", "unknown"),
            pageCount=page_count,
            markdown=markdown,
            pages=pages,
            metadata={"source": "private-upload", "filename": path.name},
        )
