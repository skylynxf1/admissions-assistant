# Repository guidance

## Scope

Preserve the distinction between the Next.js demo and the evidence-backed Python ingestion service.
Never present synthetic fixtures or sample frontend data as verified institutional guidance.

## Required invariants

- A published academic claim must resolve to at least one exact `EvidenceRecord` in its named source
  snapshot.
- Keep UW Seattle scope explicit. Do not blend Bothell or Tacoma records.
- Do not infer no credit from a missing equivalency result.
- Preserve AND/OR grouping, recommendations, footnotes, effective periods, warnings, and unknowns.
- Do not follow authenticated/NetID links or bypass robots, allowlists, rate limits, or response limits.
- Network and OpenAI calls must remain opt-in and dependency-injected in tests.
- Never log credentials, raw page bodies, or full model prompts containing source content.
- Historical evidence and record versions are append-only.

## Implementation conventions

- Python 3.12, strict mypy, Pydantic v2, async SQLAlchemy 2, FastAPI.
- Use typed stage inputs/outputs; do not create an institution-specific monolithic scraper.
- Add deterministic parsing before any model fallback.
- Add a failing test before changing behavior, then run the narrow test and full quality gate.
- Keep adapters under `src/academic_ingest/adapters/<institution>/` and generic governance outside
  institution packages.
- Use Alembic for PostgreSQL schema changes.

## Verification

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m pytest
npm run typecheck
npm run lint
npm run build
```

For schema or persistence changes, also run:

```bash
docker compose up -d postgres
python -m alembic upgrade head
python -m alembic check
```
