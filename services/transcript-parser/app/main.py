from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from pypdf import PdfReader

from app.models import ParsedDocument
from app.parsers.docling_parser import DoclingTranscriptParser
from app.parsers.pymupdf_parser import PyMuPdfTranscriptParser

app = FastAPI(title="Pathwise Transcript Parser", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/parse", response_model=ParsedDocument)
async def parse_transcript(
    file: UploadFile = File(...),
    parser: str = Query(default="docling", pattern="^(docling|marker|pymupdf)$"),
) -> ParsedDocument:
    if file.content_type != "application/pdf" and not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail={"code": "corrupt_pdf", "detail": "A PDF file is required."})
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=422, detail={"code": "empty_pdf", "detail": "The PDF is empty."})
    if len(payload) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail={"code": "parser_failed", "detail": "The PDF exceeds 15 MB."})

    suffix = Path(file.filename or "transcript.pdf").suffix or ".pdf"
    temp_path: Path | None = None
    try:
        with NamedTemporaryFile(suffix=suffix, delete=False) as temp:
            temp.write(payload)
            temp_path = Path(temp.name)
        try:
            reader = PdfReader(temp_path)
            if reader.is_encrypted:
                raise HTTPException(status_code=422, detail={"code": "protected_pdf", "detail": "Password-protected PDFs are not supported."})
        except HTTPException:
            raise
        except Exception as error:
            raise HTTPException(status_code=422, detail={"code": "corrupt_pdf", "detail": f"The PDF is corrupt: {error}"}) from error

        if parser == "marker":
            raise HTTPException(status_code=501, detail={"code": "parser_unavailable", "detail": "Marker is an optional adapter and is not installed in this image."})
        adapter = PyMuPdfTranscriptParser() if parser == "pymupdf" else DoclingTranscriptParser()
        try:
            return adapter.parse(temp_path)
        except Exception as error:
            raise HTTPException(status_code=422, detail={"code": "parser_failed", "detail": str(error)}) from error
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()
