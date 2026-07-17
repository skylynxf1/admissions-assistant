# Transcript PDF parsing pipeline

The transcript pipeline is a review-first ingestion system. It records what a PDF says; it does **not** decide transferability, equivalency, prerequisite coverage, or degree applicability.

## Processing flow

1. The Next.js upload route accepts PDF files up to 15 MB and rejects empty, non-PDF, incomplete, encrypted, or duplicate files.
2. Authenticated files are written to the private `transcript-uploads` bucket at `<user-id>/<document-id>/<filename>`.
3. A document progresses through `uploaded`, `processing`, `needs_review`, `completed`, or `failed`.
4. The private Python worker parses the PDF. Docling is primary; PyMuPDF implements the optional text-native fast path; Marker is isolated behind the same interface.
5. The server sends parser Markdown and page/block evidence to the configured OpenAI model using the strict schema in `lib/transcript/extraction-schema.ts`.
6. Deterministic code checks credit arithmetic, references, page evidence, confidence, duplicate-looking rows, GPA bounds, and printed totals.
7. Raw parser output, raw structured extraction, validation results, and editable normalized records are stored separately.
8. The user reviews every row, resolves blocking warnings, and confirms the record before planning uses it.

The no-key demo follows the same output contracts but returns conspicuously labeled fictional sample data. It never claims to have read the uploaded PDF.

## Data separation

| Layer | Tables | Mutability |
| --- | --- | --- |
| Original document | `student.transcript_documents` + private Storage object | Document metadata changes status; original PDF is private |
| Parser/model audit | `transcript_parse_runs`, `transcript_pages` | Append-only for the owning user; every retry creates a new run |
| Reviewed facts | `student_institutions`, `academic_terms`, `transcript_courses`, `exam_credits`, `transcript_summaries` | Editable by the owning user |
| Review controls | `transcript_warnings`, `transcript_review_actions` | Warning state is editable; actions are append-only |
| Academic evaluation | existing `planning.*` tables | Downstream and separate from transcript extraction |

The transcript course model intentionally contains no destination course, university requirement, or equivalency field. An extraction cannot invent an equivalency because the schema has nowhere to store one.

## Local worker setup

Use Python 3.11, then from `services/transcript-parser`:

```powershell
python -m venv .venv
.venv\Scripts\pip install -e .
.venv\Scripts\uvicorn app.main:app --port 8001
```

Set these values in `.env.local`:

```dotenv
DOCLING_SERVICE_URL=http://127.0.0.1:8001
TRANSCRIPT_MARKER_FALLBACK=false
OPENAI_API_KEY=<server-only key>
OPENAI_MODEL=gpt-5.6
```

Docling can be resource-intensive on first install. The Next.js app and sample flow do not require the worker.

## Authenticated API

All routes below require `Authorization: Bearer <Supabase access token>`.

| Method and route | Purpose |
| --- | --- |
| `POST /api/transcript-documents` | Validate, deduplicate, privately upload, and create a document |
| `GET /api/transcript-documents` | List the user's documents and statuses |
| `GET /api/transcript-documents/:id` | Return reviewed data, warnings, pages, runs, and edit history |
| `DELETE /api/transcript-documents/:id` | Delete the private object and cascaded records |
| `POST /api/transcript-documents/:id/parse` | Run Docling, structured extraction, validation, and persistence |
| `POST /api/transcript-documents/:id/retry` | Append a run using `docling`, `pymupdf`, or optional `marker` |
| `POST /api/transcript-documents/:id/confirm` | Confirm reviewed data when no blocking warning remains |
| `POST /api/transcript-documents/:id/courses` | Add a reviewed course |
| `PATCH/DELETE /api/transcript-documents/:id/courses/:courseId` | Edit or delete a reviewed course |
| `POST /api/transcript-documents/:id/exam-credits` | Add reviewed exam credit |
| `PATCH /api/transcript-documents/:id/warnings/:warningId` | Resolve or dismiss a warning |

`POST /api/transcript/extract` remains the no-auth demo boundary. It runs the live parser only when both the worker and OpenAI are configured; otherwise it returns sample output with `meta.mode = "sample"`.

## Operational follow-ups

- Move long-running parsing from the synchronous route to a durable job queue before production traffic.
- Add virus scanning and a configurable retention/deletion schedule for private PDFs.
- Store encrypted student identifiers only if the product truly needs them.
- Add rate limits, worker concurrency limits, tracing, cost metrics, and parse-quality evaluation fixtures from multiple layouts.
- Add a signed, short-lived original-PDF viewer for visual page comparison.
