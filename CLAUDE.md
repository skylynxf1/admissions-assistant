# Pathwise / admission agent

Read `AGENTS.md` first — it holds the safety invariants, evidence rules, and the
verification gate, and is authoritative for those. This file covers what AGENTS.md
doesn't: the layout of the repo, the JS↔Python boundary, and which parts are wired up
versus stubbed. `README.md` has the long-form product tour; don't duplicate it here.

## What this is

A transfer-planning prototype for students moving to UW Seattle: upload a transcript,
pick target schools/majors, get prerequisite and requirement analysis with source
citations. It is four separate codebases in one repo — a Next.js app plus three Python
FastAPI services — and most of the frontend's analysis is still mock data (see below).

## The four runtimes

| Piece | Language | Where | Runs on |
| --- | --- | --- | --- |
| Next.js app (product UI + BFF routes) | TypeScript | `app/`, `components/`, `lib/`, `data/` | :3000 |
| Transcript parser worker | Python 3.11–3.12 | `services/transcript-parser/` | :8001 |
| Course recommendation service | Python 3.12 | `services/course-recommendation/` | :8002 |
| Academic ingestion service (`academic_ingest`) | Python 3.12 | `src/academic_ingest/`, `alembic/`, `scripts/` | :8000 |

Each Python piece has its **own** `pyproject.toml` and its own virtualenv. They are not a
workspace; installing one does not install the others.

## Architecture — how the pieces actually connect

1. **Transcript upload** — `app/api/transcript*/` → `lib/transcript/pipeline.ts` →
   `lib/transcript/parsers/docling-client.ts` POSTs the PDF to
   `${DOCLING_SERVICE_URL}/parse?parser=docling` (the :8001 worker). The worker returns
   page-aware Markdown/blocks and deletes its temp file; the PDF itself stays in private
   Supabase Storage. GPT structured extraction, validation, and normalization all happen
   **in TypeScript**, not in the worker. This is the only live JS→Python call in the repo.
2. **Evidence in** — `POST /app/api/ingestion/evidence` accepts evidence payloads
   authenticated by an `x-ingestion-secret` header compared against `INGESTION_API_KEY`,
   and writes to Supabase via the service-role client.
3. **Everything else in the frontend is mocked.** `lib/services/index.ts` wires *every*
   planning capability (policy retrieval, equivalency, requirements, prerequisite graph,
   recommendations, scenario simulation, advisor) to the `Mock*` classes in
   `lib/services/mock.ts`. `app/api/simulation`, `/scenarios`, `/academic-analysis`,
   `/advisor` are served from those mocks.
4. **The recommendation service is not connected.** `RECOMMENDATION_SERVICE_URL` exists in
   `.env.example` but no TypeScript file reads it, and there is no `app/api/recommendations`
   route. Wiring it is planned work (`docs/superpowers/plans/2026-07-20-multi-source-transfer-backend.md`).
5. **The ingestion service is not connected either.** Nothing under `src/` or `scripts/`
   references Supabase or the `/api/ingestion/evidence` endpoint — the bridge from the
   ingestion Postgres to the app database is currently manual/unbuilt.

## Two databases, not one

This is the most common source of confusion:

- **Supabase** (`supabase/migrations/`, `supabase/seed.sql`) is the **application**
  database — schemas `catalog`, `source`, `policy`, `equivalency`, `student`, `planning`,
  `operations`, with RLS. Owned by the Next.js app and the recommendation service. Managed
  by the Supabase CLI (`npm run supabase:*`), never by Alembic.
- **Alembic** (`alembic/`, `alembic.ini`) manages a **separate** plain PostgreSQL database
  used only by `src/academic_ingest` — the `academic_ingest` DB started by
  `docker-compose.yml` on :5432 (`ACADEMIC_INGEST_DATABASE_URL`).

They share vocabulary (sources, snapshots, evidence, policies) but are physically distinct
stores with no automated sync. Never point Alembic at Supabase or vice versa.

## Commands

Python here is **pip + venv, not uv** — there is no `uv.lock` anywhere in the repo. Do not
run `uv add`/`uv run` in this project.

```bash
# --- JS (npm; package-lock.json) ---
npm install
npm run dev            # Next.js on :3000; full demo works with no env vars (sample data)
npm run typecheck      # tsc --noEmit
npm run lint           # eslint .
npm run build
npm test               # node --test on tests/*.test.ts  (TS tests only)
npm run supabase:start / :reset / :lint / :stop   # needs Docker Desktop
npm run supabase:types # regenerate lib/supabase/database.types.ts after every migration

# --- Python: academic_ingest (repo root, root .venv) ---
python -m pip install -e ".[dev]"
python -m ruff check . && python -m ruff format --check .
python -m mypy src                # strict
python -m pytest                  # testpaths=tests, asyncio_mode=auto
docker compose up -d postgres     # required for -m postgres tests and alembic
python -m alembic upgrade head
python -m alembic check
python -m uvicorn academic_ingest.api.app:create_app --factory --reload   # :8000

# --- Python: transcript parser (own venv, Python 3.11) ---
cd services/transcript-parser && python -m venv .venv
.venv/Scripts/pip install -e .
.venv/Scripts/uvicorn app.main:app --port 8001

# --- Python: course recommendation (own venv, Python 3.12) ---
cd services/course-recommendation && py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[test]"
.venv\Scripts\uvicorn.exe app.main:app --reload --port 8002
.venv\Scripts\python.exe -m pytest        # its own suite, NOT covered by root pytest
```

The full pre-merge gate is the block at the bottom of `AGENTS.md`; run that, not a subset.

## Folder notes

- `src/academic_ingest/` — ingestion pipeline: `fetching/`, `snapshots/`, `adapters/<institution>/`,
  `extraction/`, `normalization/`, `conflicts/`, `review/`, `publishing/`, `api/`, `db/`.
- `config/institutions/` — per-institution allowlists and source boundaries; edit this, not
  the adapter, to change what may be fetched.
- `data/` — frontend sample data (fictional). `tests/fixtures/uw/` — synthetic UW fixtures.
- `scripts/` — ingestion CLIs (`ingest_uw_sample.py --fixture-only`, `export_uw_records.py`,
  `inspect_uw_sources.py`), root-venv Python.
- `docs/` — `BACKEND.md` (Supabase), `TRANSCRIPT_PIPELINE.md`, `data-model.md`, `pipeline.md`,
  `uw-source-map.md`, `safety-and-compliance.md`.
- `.worktrees/` — a git worktree duplicate of this repo. Ignore it; never edit files there.

## Dangerous areas

- `app/api/ingestion/evidence/route.ts` — the only trusted-write path into Supabase. It uses
  a timing-safe compare on `INGESTION_API_KEY` and the service-role client. Weakening the
  comparison, or letting `INGESTION_API_KEY` / `SUPABASE_SERVICE_ROLE_KEY` acquire a
  `NEXT_PUBLIC_` prefix, exposes full-database write access to the browser.
- `supabase/migrations/` — RLS policies and schema grants live here. A migration that relaxes
  a `student`/`planning` ownership policy leaks other users' transcripts. `supabase/schema.sql`
  and `combined_setup.sql` are derived convenience dumps; the numbered migrations are canonical.
- `alembic/versions/` — excluded from ruff. Evidence and record versions are append-only
  (AGENTS.md); a migration that rewrites or drops history violates that invariant.
- `config/institutions/` + `src/academic_ingest/fetching/` — robots, allowlist, and rate-limit
  enforcement. Live network is opt-in via `ACADEMIC_INGEST_NETWORK_ENABLED`; keep it failing closed.
- `.env.local` holds real keys — never read or echo it. Add new variable names to `.env.example`
  with empty values only.

## Known edge cases

- `npm test` and `python -m pytest` both target `tests/`. That directory holds Python tests
  (`unit/`, `integration/`, `conftest.py`) *and* `transcript-validator.test.ts`. Each runner
  ignores the other's files — but adding a test there means picking the right runner.
- Root `pytest` does **not** collect `services/*/tests`. The recommendation service's suite
  must be run from its own directory with its own venv.
- Tests marked `postgres` need `docker compose up -d postgres`; without it they fail on
  connection, not on logic.
- The marker parser adapter (`lib/transcript/parsers/marker-client.ts` → worker) returns `501`
  by design until its dependency is installed. `TRANSCRIPT_MARKER_FALLBACK=false` by default.
- With no Supabase credentials the recommendation service serves a labeled fictional scenario
  at ID `90000000-0000-0000-0000-000000000001`. Never treat its output as real guidance.
- Python versions differ per service: transcript parser allows 3.11, the other two pin
  `>=3.12,<3.13`. A single shared venv will not satisfy all three.

## Keeping this file current

Safety/evidence invariants and the verification gate belong in `AGENTS.md`. Architecture,
commands, and gotchas belong here. When something below turns out to be wrong, fix it in
place rather than adding a correction elsewhere.
