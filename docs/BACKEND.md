# Pathwise Supabase backend

This backend implements the evidence-to-evaluation separation required by the product and scraping specifications. The app still runs without Supabase; when configured and authenticated, the same UI can persist transcripts and scenarios through the server routes.

## Data domains

| Schema | Responsibility | Write access |
| --- | --- | --- |
| `source` | Official domains, source pages, immutable snapshots, exact evidence, provenance links | Trusted ingestion only |
| `catalog` | Institutions, catalogs, colleges, departments, courses, versions, offerings, programs | Trusted ingestion only |
| `policy` | Normalized requirements, nested expression trees, transfer policies, exam-credit rules | Trusted ingestion only |
| `equivalency` | Many-to-many course mappings with distinct `not_found`, `no_credit`, and `manual_review` outcomes | Trusted ingestion only |
| `student` | Profiles, private uploads, transcripts, courses, exams, goals, constraints, corrections | Owning user through RLS |
| `planning` | Scenarios and derived evaluations, readiness, recommendations, unresolved questions, advisor history | Owning user; derived results are written server-side |
| `operations` | Crawl/parser jobs, conflicts, review queues, change events | Trusted operations only |

The central rule is enforced structurally: source records never contain student conclusions, and planning results never overwrite source or policy rows. `planning.course_evaluations` only permits a direct equivalent when its verification status is `confirmed`.

## Local setup

1. Install Docker Desktop and make sure its engine is running. The Supabase CLI is pinned as a project development dependency.
2. Start the local stack and apply migrations:

   ```bash
   npm run supabase:start
   npm run supabase:reset
   ```

3. Copy the values printed by `supabase status` into `.env.local`:

   ```dotenv
   NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
   NEXT_PUBLIC_SUPABASE_ANON_KEY=<local anon key>
   SUPABASE_SERVICE_ROLE_KEY=<local service role key>
   INGESTION_API_KEY=<a random server-only secret>
   ```

4. Start Next.js with `npm run dev`.

`supabase/seed.sql` contains labeled sample institutions and programs for local development. It does not represent verified policy data.

## Hosted Supabase setup

1. Create and link a Supabase project.
2. Run `supabase db push`.
3. In the project's API settings, expose these schemas: `public`, `catalog`, `source`, `policy`, `equivalency`, `student`, and `planning`.
4. Add the project URL, anon key, service-role key, and ingestion secret to the server environment.
5. Keep `SUPABASE_SERVICE_ROLE_KEY` and `INGESTION_API_KEY` server-only. Never add `NEXT_PUBLIC_` to either name.
6. Regenerate database types after every migration:

   ```bash
   npx supabase gen types typescript --linked > lib/supabase/database.types.ts
   ```

## Security model

- Catalog, normalized policy, and approved evidence are readable through the Data API.
- Pending or rejected evidence is hidden from public clients.
- Student and planning tables use `auth.uid()` ownership policies.
- Transcript PDFs are private and must be stored under `<user-id>/...` in `transcript-uploads`.
- The service role is reserved for ingestion and writing derived evaluation results.
- The evidence endpoint uses a separate `x-ingestion-secret` defense in addition to the service role held only by the server.
- Scenario and transcript routes require a Supabase bearer access token; the app remains local-only without one.

## Backend routes

| Route | Auth | Purpose |
| --- | --- | --- |
| `GET /api/backend/health` | None | Reports configuration state without returning secrets |
| `GET /api/scenarios` | User bearer token | Lists the current user's active scenarios |
| `POST /api/scenarios` | User bearer token | Saves scenario inputs and an optional derived result |
| `POST /api/transcripts` | User bearer token | Saves the editable transcript, course records, and exam scores |
| `GET/POST /api/transcript-documents` | User bearer token | Lists or privately uploads transcript PDFs with hash deduplication |
| `GET/DELETE /api/transcript-documents/:id` | User bearer token | Reads a review bundle or deletes its private document and records |
| `POST /api/transcript-documents/:id/parse` | User bearer token | Runs Docling, strict extraction, deterministic validation, and normalization |
| `POST /api/transcript-documents/:id/retry` | User bearer token | Appends a parser run without overwriting prior evidence |
| `POST /api/transcript-documents/:id/confirm` | User bearer token | Confirms reviewed facts after blocking warnings are resolved |
| `POST /api/ingestion/evidence` | `x-ingestion-secret` | Upserts a page/snapshot and inserts pending evidence claims |

The analysis, simulation, and advisor routes still use sample academic-policy services. Transcript extraction has its own production boundary and uses labeled sample output only when the parser/model stack is unavailable. See [TRANSCRIPT_PIPELINE.md](TRANSCRIPT_PIPELINE.md).

## Evidence ingestion contract

Every evidence payload must include an institution, original and canonical URL, source type, retrieval timestamp, content hash, and exact claims. Each claim includes the exact quote, a locator, confidence, normalized value, and review status. New claims default to `pending`; they are not public until reviewed and approved.

```json
{
  "institutionId": "10000000-0000-0000-0000-000000000001",
  "originalUrl": "https://example.edu/catalog",
  "canonicalUrl": "https://example.edu/catalog",
  "sourceType": "catalog",
  "official": true,
  "retrievedAt": "2026-07-16T20:00:00Z",
  "contentHash": "sha256:...",
  "evidence": [
    {
      "claimKey": "course.math-124.credits",
      "claimType": "course_credits",
      "exactQuote": "MATH 124 ... 5 credits",
      "locator": { "heading": "MATH 124" },
      "normalizedValue": { "credits": 5 },
      "confidence": "high"
    }
  ]
}
```

Raw HTML/PDF/JSON/CSV bodies should normally live in a private ingestion bucket, with `source.snapshots.storage_path` holding the location and `content_hash` providing deduplication. `raw_text` is available for short extracted text but should not become the primary binary store.
