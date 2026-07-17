# Pathwise academic planning and UW Seattle ingestion

Pathwise combines the existing Next.js academic-planning prototype with a production-oriented
Python service for ingesting University of Washington Seattle catalog, admissions, transfer, major,
and AP-credit evidence.

The ingestion service is conservative by design: every published claim carries an exact quote from
an immutable source snapshot, unresolved logic stays unresolved, conflicting official claims are
sent to review, and live network access is disabled unless an operator explicitly enables it.

> The saved HTML fixtures and frontend scenarios are synthetic test/demo data. They do not replace
> advice from UW Admissions, the Registrar, an academic department, or an adviser.

## What is implemented

- Typed Pydantic domain models and matching SQLAlchemy/PostgreSQL schema
- Content-addressed source snapshots, change events, ETag support, and append-only record versions
- SSRF-resistant, allowlisted HTTPS fetching with response limits, rate limits, retries, redirects,
  conditional requests, robots handling, and network opt-in
- UW adapters for the course catalog/glossary, majors, major details, transfer admissions/policies,
  AP credit, the public Time Schedule boundary, and Equivalency Guide discovery
- Recursive prerequisite AST parsing and three-state evaluation: satisfied, unsatisfied, unresolved
- Exact-evidence validation, logical validation, conflict detection, explainable confidence scoring,
  human-review routing, and transactional publication
- Optional GPT-5.6 structured extraction behind dependency injection; normal tests use a fake client
- FastAPI endpoints for fixture ingestion, sources, records, conflicts, review tasks, and crawl jobs
- Offline sample ingestion, normalized JSON export, structured logging, and 12 governance QA cases

## Backend quick start

Requirements: Python 3.12 and Docker (for PostgreSQL verification).

```bash
python -m pip install -e ".[dev]"
docker compose up -d postgres
python -m alembic upgrade head
python -m uvicorn academic_ingest.api.app:create_app --factory --reload
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for the generated API documentation.

Configuration is read from `ACADEMIC_INGEST_*` variables. See [.env.example](.env.example) and
[config/institutions/uw_seattle.yaml](config/institutions/uw_seattle.yaml). Live acquisition requires
both `ACADEMIC_INGEST_NETWORK_ENABLED=true` and a contact email.

## Safe offline sample and export

No network or OpenAI credential is used by these commands:

```bash
python scripts/ingest_uw_sample.py --fixture-only
python scripts/export_uw_records.py --output tmp/uw-records.json
python scripts/inspect_uw_sources.py
```

`inspect_uw_sources.py` reports `network_disabled` unless `--allow-network` is present. A live
inspection also requires `ACADEMIC_INGEST_CONTACT_EMAIL`; it checks the institution allowlist,
fetches and evaluates robots.txt, fails closed when robots policy is unavailable, and never prints
page bodies.

## API overview

- `GET /health`
- `POST /crawl-jobs`, `GET /crawl-jobs/{id}`
- `POST /pages/ingest` for a local HTML/PDF fixture
- `GET /sources`, `GET /sources/{id}`
- `GET /courses`, `GET /courses/{id}`
- `GET /programs`, `GET /programs/{id}`
- `GET /admissions-rules`, `/transfer-policies`, `/exam-credit`
- `GET /conflicts`, `GET /review-tasks`
- `POST /review-tasks/{id}/resolve`

Record detail includes evidence and version history. Review resolution appends reviewer metadata and
does not modify the original evidence.

## Frontend quick start

Requirements: Node.js 20+. The frontend remains a demo experience and uses labeled sample services.

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and choose **Transfer planning**.

1. Select Transfer Planning.
2. Complete the short student profile.
3. Upload a PDF for sample extraction or choose manual entry, then review and edit every course field.
4. Search for destination schools, check multiple options, and choose one priority school.
5. Pick one or more priority-school majors and read the short requirement outline.
6. Open the planning playground and drag recommended courses into editable quarter templates.
7. Use the simulator to add or remove schools, majors, transcript courses, grades, AP/IB credit, and planned courses.
8. Change current school/type, residency, enrollment term, maximum quarterly load, summer attendance, and graduation target.
9. Watch transfer and major eligibility, missing prerequisites, general education, credits, timeline, and open options recalculate.
10. Save multiple scenarios in the Compare tab, restore any version, or export the visible plan as a readable PDF.
11. Open Verification to distinguish confirmed, likely, unclear, manual-evaluation, and conflicting results; inspect every checked source and draft an exact-context email for unresolved items.
12. Ask the grounded advisor a question or review the sample source records behind the plan.

## Verification safeguards

The typed verification layer stores the status, source course, institution, term, destination school,
exact question, responsible office, and the outcome of each checked source. A destination course is
only displayed when a saved source explicitly contains that mapping. Unresolved results never infer
an equivalency; they explain the gap and can generate a reviewable email draft without sending it.

## Simulator coverage

The playground keeps all editable inputs in the typed scenario, transcript, and target-school models.
The mock simulation service—not the UI—calculates transfer eligibility, major readiness,
prerequisite gaps, general-education progress, projected transferable credit, estimated remaining
credit, graduation timing, term overloads, GPA, and the academic options that remain open. Saved
comparison plans capture the complete scenario and can be restored during the session.

## Quality gates

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m pytest
npm run typecheck
npm run lint
npm run build
```

The Python suite is offline by default and requires neither a network connection nor an OpenAI key.

## Repository map

- `src/academic_ingest/` — acquisition, adapters, models, governance, persistence, jobs, and API
- `config/institutions/` — institution-specific boundaries and seed URLs
- `alembic/` — PostgreSQL migrations
- `scripts/` — inspection, fixture ingestion, and evidence-preserving export
- `tests/fixtures/uw/` — synthetic, deterministic UW-shaped fixtures
- `docs/uw-source-map.md` — inspected source inventory and access decisions
- `docs/uw-adapter.md` — UW adapter behavior and known boundaries
- `docs/data-model.md` — entities, evidence, versions, conflicts, and review
- `docs/pipeline.md` — typed ingestion stages and failure isolation
- `docs/adding-an-institution.md` — extension guide
- `docs/safety-and-compliance.md` — network, privacy, retention, and untrusted-input controls
- `app/`, `components/`, `lib/`, `data/` — existing Next.js prototype

## Current limitations

- Live source inspection is opt-in; automated live publication is intentionally not the default.
- Time Schedule support is limited to public pages and never follows NetID-protected details.
- The Equivalency Guide is discovery/snapshot only until a stable public surface is confirmed.
- Missing mappings never become “no credit”; only explicit source language can create that outcome.
- “Data Science” is retained as an Informatics curricular option when that is what the source states,
  not invented as a separate UW Seattle major.
- Model-assisted extraction cannot assign final confidence or bypass deterministic evidence gates.
