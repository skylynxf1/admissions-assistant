from pathlib import Path

import fitz

from app.models import ParsedBlock, ParsedDocument, ParsedPage
from app.parsers.base import TranscriptParser


class PyMuPdfTranscriptParser(TranscriptParser):
    def parse(self, path: Path) -> ParsedDocument:
        document = fitz.open(path)
        pages: list[ParsedPage] = []
        for page_index, page in enumerate(document):
            page_number = page_index + 1
            text = page.get_text("text").strip()
            blocks = []
            for block_index, block in enumerate(page.get_text("blocks")):
                x0, y0, x1, y1, block_text, *_ = block
                blocks.append(ParsedBlock(id=f"pymupdf-{page_number}-{block_index}", pageNumber=page_number, type="text", text=block_text.strip(), boundingBox=(x0, y0, x1, y1)))
            pages.append(ParsedPage(pageNumber=page_number, markdown=text, text=text, blocks=blocks))
        markdown = "\n\n".join(f"## Page {page.pageNumber}\n\n{page.markdown}" for page in pages)
        if not markdown.strip():
            raise ValueError("PyMuPDF returned no readable transcript content.")
        return ParsedDocument(parser="pymupdf", parserVersion=fitz.VersionBind, pageCount=len(pages), markdown=markdown, pages=pages, metadata={"source": "private-upload", "filename": path.name})
