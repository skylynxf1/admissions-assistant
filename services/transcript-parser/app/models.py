from typing import Any, Literal

from pydantic import BaseModel, Field


class ParsedBlock(BaseModel):
    id: str
    pageNumber: int = Field(ge=1)
    type: Literal["text", "table", "heading", "other"]
    text: str
    boundingBox: tuple[float, float, float, float] | None = None


class ParsedPage(BaseModel):
    pageNumber: int = Field(ge=1)
    markdown: str
    text: str
    blocks: list[ParsedBlock]


class ParsedDocument(BaseModel):
    parser: Literal["docling", "marker", "pymupdf", "sample"]
    parserVersion: str
    pageCount: int = Field(ge=1)
    markdown: str
    pages: list[ParsedPage]
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class ParserFailure(BaseModel):
    code: Literal["protected_pdf", "corrupt_pdf", "empty_pdf", "parser_unavailable", "parser_failed"]
    detail: str
