# Transcript parser worker

This private Python service converts a transcript PDF into page-aware Markdown and parser blocks. Docling is the primary parser. PyMuPDF is available as an optional fast path for text-native PDFs; the Marker adapter is intentionally isolated and returns `501` until its dependency is installed.

Run locally with Python 3.11:

```bash
python -m venv .venv
.venv/Scripts/pip install -e .
.venv/Scripts/uvicorn app.main:app --port 8001
```

Set `DOCLING_SERVICE_URL=http://127.0.0.1:8001` in the Next.js environment. The service does not persist uploads: it uses a temporary file and deletes it after parsing. The original stays in the user's private Supabase Storage path.
