# Pathwise academic planning platform

Pathwise combines a Next.js transfer-planning prototype with three isolated backend capabilities:

- a Supabase-backed planning, transcript, evidence, and simulation data model;
- an evidence-preserving UW Seattle ingestion service contributed through PR #1;
- deterministic transcript parsing and course recommendation services.

The product supports editable transcripts, multiple universities and majors, scenario simulation, prerequisite analysis, ranked course recommendations, uncertainty escalation, source citations, and advisor chat.

> **Demo-data warning:** frontend policy summaries, seed courses, offerings, equivalencies, and in-memory recommendation results are fictional sample data. They are not verified official academic guidance. The UW ingestion fixtures are synthetic. Final academic decisions belong to the institution.

## Frontend quick start

Requirements: Node.js 22+, npm or pnpm, and optionally Docker Desktop for local Supabase.

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and choose **Transfer planning**. The complete demo flow works without API keys by using clearly labeled sample data.

Quality checks:

```bash
npm run typecheck
npm run lint
npm run build
```

## Local Supabase

The checked-in migrations create domain-separated `catalog`, `source`, `policy`, `equivalency`, `student`, `planning`, and `operations` schemas with RLS, indexes, private transcript storage, prerequisite rules, recommendation weights, and caching.

```bash
npm run supabase:start
npm run supabase:reset
npm run supabase:lint
```

Copy the local URL and keys into `.env.local`. See [docs/BACKEND.md](docs/BACKEND.md). The seed is explicitly fictional and exists only to exercise the prototype.

## UW Seattle evidence ingestion service

Andrew's ingestion service is a Python 3.12/FastAPI/PostgreSQL pipeline under `src/academic_ingest`. It provides allowlisted acquisition, robots checks, immutable snapshots, UW-specific adapters, exact evidence, versioned records, conflict detection, human review, and conservative publication gates.

```bash
python -m pip install -e ".[dev]"
docker compose up -d postgres
python -m alembic upgrade head
python -m uvicorn academic_ingest.api.app:create_app --factory --reload
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). Live network access is disabled unless `ACADEMIC_INGEST_NETWORK_ENABLED=true` and a contact email is configured. Fixture inspection and tests remain offline by default.

```bash
python scripts/ingest_uw_sample.py --fixture-only
python scripts/export_uw_records.py --output tmp/uw-records.json
python scripts/inspect_uw_sources.py
```

## Transcript parser

The private Docling-first worker converts PDFs into page-aware Markdown and parser blocks. GPT structured extraction, deterministic validation, editable normalization, warnings, and confirmation are handled by the Next.js transcript pipeline. See [docs/TRANSCRIPT_PIPELINE.md](docs/TRANSCRIPT_PIPELINE.md) and [services/transcript-parser/README.md](services/transcript-parser/README.md).

## Course recommendation service

The Python 3.12/FastAPI/NetworkX service deterministically evaluates relational ALL/ANY/MIN_COUNT prerequisite groups, traverses direct and transitive chains, filters candidates, measures multi-program and multi-university value, calculates risk, and returns a full weighted score breakdown.

```powershell
cd services/course-recommendation
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[test]"
.venv\Scripts\uvicorn.exe app.main:app --port 8002
```

Without Supabase credentials it serves a labeled fictional scenario at ID `90000000-0000-0000-0000-000000000001`. Full scoring and API documentation is in [services/course-recommendation/README.md](services/course-recommendation/README.md).

GPT may explain structured recommendation facts, but it cannot calculate eligibility, alter scores, satisfy prerequisites, invent offerings, or invent equivalencies.

## Primary planning journey

1. Select Transfer Planning and complete the short profile.
2. Upload a transcript PDF or enter courses manually, then edit and verify every extracted field.
3. Search for multiple destination schools and choose one priority school.
4. Add multiple majors and review the priority program outline.
5. Open the planning playground and drag recommended courses into editable quarter templates.
6. Change institutions, majors, residency, school type, grades, AP/IB credit, enrollment term, credit load, and graduation target.
7. Review recalculated eligibility, prerequisites, general education, credit estimates, timeline, open options, and uncertainty.
8. Compare saved plans, export a readable PDF, inspect evidence, draft a verification email, or ask the grounded advisor.

## Safety boundaries

- Missing mappings never become “no credit”; only explicit structured evidence can produce that outcome.
- Course equivalency, general education, program application, prerequisite eligibility, and recommendation score remain separate concerns.
- Unknown or unresolved prerequisite conditions are never treated as satisfied.
- Recommendation reasons are generated from deterministic features and include source IDs.
- Graduation acceleration is conservative and never claims an exact date when offering data is incomplete.
- Raw ingestion bodies stay in immutable snapshots and are excluded from public record exports.
- Network ingestion is opt-in, host-limited, rate-limited, and fails closed when policy cannot be verified.

## Combined quality gates

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m pytest
npm run typecheck
npm run lint
npm run build
npm run supabase:lint
```

The recommendation service has its own 29-test suite under `services/course-recommendation/tests`.

## Repository map

- `app/`, `components/`, `lib/`, `data/` — Next.js product and service boundaries
- `supabase/migrations/`, `supabase/seed.sql` — application database, RLS, and fictional seed
- `services/transcript-parser/` — private Docling transcript worker
- `services/course-recommendation/` — prerequisite graph and deterministic ranking API
- `src/academic_ingest/` — UW acquisition, adapters, governance, persistence, jobs, and API
- `config/institutions/` — institution-specific source boundaries
- `alembic/` — ingestion-service PostgreSQL migrations
- `scripts/` — source inspection, fixture ingestion, and evidence-preserving export
- `tests/fixtures/uw/` — synthetic UW-shaped fixtures
- `docs/BACKEND.md` — Supabase and application API setup
- `docs/product-spec.md` — original planning product specification
- `docs/uw-source-map.md`, `docs/uw-adapter.md`, `docs/data-model.md`, `docs/pipeline.md` — ingestion architecture
- `docs/safety-and-compliance.md` — network, privacy, retention, and untrusted-input controls

## Current limitations

- Only Transfer Planning has the complete frontend workflow.
- Live source inspection and publication are intentionally not automatic.
- Time Schedule support is limited to public pages and never follows NetID-protected details.
- The UW Equivalency Guide remains discovery/snapshot-only until a stable public surface is confirmed.
- Multi-term optimization, OR-Tools scheduling, course conflicts, cost optimization, and preference optimization are Phase 2 work.
