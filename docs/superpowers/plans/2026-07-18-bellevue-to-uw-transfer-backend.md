# Bellevue College to UW Seattle Backend Implementation Plan

> **Handoff note:** Continue on `andrew`. Do not change `main`. Execute each task test-first and keep synthetic/sample data visibly separate from verified institutional guidance.

**Goal:** Deliver the approved Bellevue College to UW Seattle evidence-backed transfer workflow: official-source ingestion, exact transfer resolution, immutable confirmed transcripts, multi-major analysis, and a deadline-aware Bellevue course plan.

**Architecture:** The Python/FastAPI service is the sole authority for public academic facts, evidence, mappings, analysis, and planning. Supabase remains the authenticated store for private student documents and immutable transcript revisions. Next.js is a typed client. Cross-boundary requests use opaque revision IDs and content hashes; academic facts are not independently writable in both databases.

**Stack:** Python 3.12, Pydantic v2, FastAPI, async SQLAlchemy 2, Alembic/PostgreSQL, Next.js/TypeScript, Supabase, pytest, Ruff, mypy, Vitest.

## Checkpoint at handoff

- Branch: `andrew`
- Design: `docs/superpowers/specs/2026-07-18-bellevue-to-uw-transfer-backend-design.md`
- The design commit is present on `andrew`; no production behavior has been changed yet.
- Baseline verified in the isolated `andrew` worktree:
  - Python: `122 passed` (one Starlette deprecation warning)
  - Frontend: `4 passed` (one Node typeless-package warning)
- `main` was not modified by this work.
- On Windows/OneDrive, create the Python 3.12 virtual environment outside the repository and use a `.venv` junction if in-repo venv files become locked or hard-linked.

## Non-negotiable contracts

1. Every published academic claim resolves through a real foreign key to at least one exact `EvidenceRecord` in the named immutable snapshot.
2. UW Seattle scope is explicit. Reject Bothell and Tacoma identifiers before evaluation.
3. A missing equivalency lookup is `not_found`, never `explicit_no_credit`. It is a snapshot-scoped lookup observation, not a fabricated positive quote.
4. Preserve AND/OR/CHOOSE-N/sequence/concurrency structure, conditions, recommendations, footnotes, warnings, effective periods, and unknowns.
5. If an effective-date rule is not explicit, return `cannot_determine`; do not guess which term controls.
6. Historical source, record, transcript, analysis, and plan versions are append-only.
7. Analysis binds to one immutable confirmed transcript revision and exact program/mapping/evidence versions.
8. General transfer and every selected major are evaluated separately. Shared projections never replace the original logical trees.
9. Readiness is descriptive; never return a probability or an invented percentage.
10. Plans recommend Bellevue courses only. Missing schedule evidence means availability is unknown and must not exclude or advertise a course.
11. Network and model calls remain opt-in and dependency-injected. Tests use offline fixtures.
12. Never log credentials, raw page bodies, student documents, or full prompts containing source content.

## Known architecture defects to address

- `validation/source_scope.py` is hard-coded to UW/Seattle and cannot validate an institution-configured Bellevue source.
- Publication stores generic record versions while several normalized academic tables are largely unused. Do not create a second independently writable academic truth surface.
- `record_versions.evidence_record_ids` is JSON rather than an enforced evidence relationship, and the low-level repository can bypass the publish gate.
- A source history of A -> B -> A can incorrectly reuse the old A row instead of appending/selecting a new current version.
- Program and requirement identities are unstable; the program detail endpoint currently can return requirements belonging to other programs.
- The UW equivalency adapter only discovers/snapshots pages; it does not parse Bellevue mappings.
- Python, Supabase, and the recommendation service use incompatible transfer-state vocabularies.
- Existing reviewed transcript rows are mutable/delete-and-reinsert, not immutable confirmed revisions.
- Existing program requirements flatten logical structure, and parsed prerequisite ASTs are not normally persisted.
- Existing mock analysis can be persisted alongside future production results.
- The recommendation service treats OR alternatives as mandatory graph edges and filters courses when offering data is absent, contrary to the approved design.

## Task 1: Enforce publication integrity and append-only version selection

**Files:**

- Modify `src/academic_ingest/db/models.py`
- Modify `src/academic_ingest/db/repositories.py`
- Modify `src/academic_ingest/publishing/service.py`
- Modify `src/academic_ingest/validation/source_scope.py`
- Add an Alembic revision under `alembic/versions/`
- Add/modify focused tests under `tests/db/`, `tests/publishing/`, and `tests/validation/`

**TDD steps:**

1. Add failing tests proving that direct publication without validated evidence is impossible, evidence relationships use foreign keys, scope comes from the institution/source config, and A -> B -> A creates/selects a new current version without mutating historical payloads.
2. Run the narrow tests and observe the expected failures.
3. Add stable academic entity identity, immutable record versions, a normalized record-version/evidence link, and a separate current/head mechanism or equivalent append-only selection.
4. Route every write through `PublishingService`; make the lower repository require a validated publication input.
5. Preserve existing data with an Alembic migration and add migration tests.
6. Run narrow tests, Ruff, mypy, and the full Python suite. Commit only this slice.

## Task 2: Add pathway capabilities and stable searchable catalogs

**Files:**

- Add `src/academic_ingest/pathways/`
- Extend institution/source configuration under `config/institutions/`
- Add `src/academic_ingest/adapters/bellevue/course_catalog.py` only after verifying an approved public official source
- Modify course/program domain identity and repositories
- Add typed schemas/routes for pathway capabilities and catalog search
- Add offline Bellevue and UW fixtures plus API/repository tests

**TDD steps:**

1. Add failing tests for the pathway `bellevue-college:uw-seattle`, stable institution-qualified IDs, case-insensitive code/title search, deterministic pagination, evidence status, and campus rejection.
2. Add a pathway registry that names source institution, destination institution/campus, supported capabilities, and configured source policies.
3. Generalize source validation from hard-coded UW checks to injected allowlisted policies while retaining the UW Seattle destination guard.
4. Implement indexed repository search; do not filter the full JSON record set in route code.
5. Configure and fixture the official public Bellevue catalog only after its exact domain/path/robots policy is reviewed. Until then, report the Bellevue catalog capability as unavailable rather than publish incomplete course metadata.
6. Return typed paginated responses with stable IDs, credits/effective periods, and evidence status.

## Task 3: Parse, publish, and resolve Bellevue equivalencies

**Files:**

- Add `src/academic_ingest/equivalencies/models.py`
- Add `src/academic_ingest/equivalencies/resolver.py`
- Extend `src/academic_ingest/adapters/uw/equivalency_guide.py`
- Align transfer states in `src/academic_ingest/models/enums.py`
- Add persistence/Alembic changes and exact structured-table fixtures/tests

**TDD steps:**

1. Add failing parser tests for one-to-one, one-to-many, many-to-one, sequence, alternatives, conditional rows, elective/general credit, explicit no credit, notes/footnotes, and effective periods.
2. Add failing resolver tests for all nine public states: `direct_equivalent`, `course_sequence_equivalent`, `elective_or_general_credit`, `transferable_no_direct_equivalent`, `explicit_no_credit`, `not_found`, `conflicting_evidence`, `manual_review_required`, and `cannot_determine`.
3. Model source components, destination components, grouping operators, conditions, credits, restrictions, duplicate-credit rules, effective periods, and evidence links without flattening.
4. Parse deterministically. Unsupported or ambiguous structure creates a review task and cannot publish a confident mapping.
5. Make `not_found` a deterministic complete-snapshot lookup observation containing normalized query, snapshot ID, index/parser version, and search trace. Never generate an evidence quote for absence.
6. Resolve exactly one high-level state while returning all detailed outcomes and separating transferability, UW credit, degree applicability, and major applicability.

## Task 4: Create immutable confirmed transcript revisions

**Files:**

- Add a Supabase migration for transcript revisions, entries, review items, and confirmation events
- Modify `lib/backend/repositories/transcript-repository.ts`
- Modify the transcript pipeline repository and authenticated Next.js transcript routes
- Add a typed Python `TranscriptRevisionProvider` interface; do not store raw student documents in the academic database
- Add repository, route, authorization, and revision-invalidation tests

**TDD steps:**

1. Add failing tests proving edits create a new draft, confirmation freezes a revision, old revisions remain readable, and analysis can consume only a confirmed Bellevue revision.
2. Preserve raw extracted and normalized values for code, title, term, credits, grade, status, and institution.
3. Represent repeats, withdrawals, failures, pass/fail, transferred-in, exam credit, and in-progress work explicitly; prevent double counting.
4. Keep document access behind existing Supabase auth/RLS. Expose only a typed confirmed-revision projection and content hash to the Python analysis service.
5. Record append-only confirmation events. Never delete/reinsert facts belonging to an already confirmed revision.

## Task 5: Persist recursive requirements and stable program relationships

**Files:**

- Strengthen `src/academic_ingest/prerequisites/{ast,parser,evaluator}.py`
- Modify UW course and major-detail adapters
- Modify program/requirement persistence and API routes
- Add stable node/rule IDs, parse metadata, evidence traces, and round-trip tests

**TDD steps:**

1. Add failing tests for nested `(A and B) or choose 2 of (C, D, E)`, sequence/concurrency, scoped minimum grades, recommendations, and critical footnotes.
2. Add failing identity tests proving unchanged reingestion preserves entity keys and every requirement references the correct stable program plus exact program version.
3. Treat ambiguous modifier scope as unresolved/review-required.
4. Persist recursive expressions and source/evidence metadata for both course prerequisites and program requirements.
5. Fix `GET /programs/{id}` so it cannot return another program's requirements.
6. Add deterministic evaluation traces and explicit completed/in-progress/missing/unknown/conflicting/confirmation-required states.

## Task 6: Implement reproducible multi-major analysis

**Files:**

- Add `src/academic_ingest/analysis/{models,coursework,evaluator,readiness,service}.py`
- Add typed API schemas/routes and register them in FastAPI
- Add fixture-backed unit, service, and API tests

**TDD steps:**

1. Add failing tests for two majors with independent trees, a display-only shared projection, different minimum grades, OR/CHOOSE-N, in-progress work, conflicts, stale evidence, elective-credit non-applicability, and campus rejection.
2. Define a request containing pathway ID, confirmed transcript revision ID, selected program version IDs, and `effective_at`. Unknown or unresolved canonical IDs return 422.
3. Evaluate general transfer independently, then each program, then create shared projections referencing existing result IDs.
4. Use deterministic readiness precedence: manual confirmation, insufficient evidence, missing verified requirements, ready after current coursework, ready from published requirements, plus a separate preparation recommendation overlay.
5. Return rule traces and a reproducibility envelope containing transcript hash/revision, every input record version, evidence snapshots/effective dates, evaluator/rule-set versions, campus/pathway IDs, canonical input hash, substantive result hash, and generation time.
6. Exclude `generated_at` from the substantive hash; identical versioned inputs must produce byte-equivalent substantive output.

## Task 7: Implement the transfer-term planner

**Files:**

- Add `src/academic_ingest/planning/{models,term_slots,solver,service}.py`
- Add typed plan schemas/routes
- Port only the valid deterministic primitives from `services/course-recommendation/`; do not create a second policy authority
- Add planner unit/service/API tests

**TDD steps:**

1. Add failing tests for prerequisite chains, feasible OR branches, CHOOSE-N, optional-edge cycles, total term-credit limits, summer inclusion, shared-major coverage, duplicate/exam/transferred-in/exclusion rules, unknown availability, and infeasible deadlines.
2. Consume a completed, non-stale analysis result rather than raw frontend policies.
3. Generate planning slots after the current term and before the intended transfer term.
4. Select verified missing required leaves first; keep confirmation-required alternatives labeled and unsatisfied.
5. Plan on logical groups/hyperedges. A simple directed graph may be only an adjacency index and must not turn alternatives into mandatory prerequisites.
6. Rank deterministically by required status, prerequisite bottleneck, number of selected majors served, deadline, credits, then canonical course ID.
7. Pack by prerequisite order and total slot credits. Label results `planning_slot`; do not claim a course is offered without separately ingested schedule evidence.
8. Return `infeasible`, `unresolved`, or `confirmation_required` with blocking reasons instead of inventing a valid schedule.

## Task 8: Connect typed UI routes and isolate sample data

**Files:**

- Replace production behavior in `app/api/academic-analysis/route.ts` and `app/api/simulation/route.ts` with authenticated thin clients to FastAPI
- Tighten scenario persistence and provenance
- Keep `lib/services/mock.ts` demo-only
- Add contract/integration tests

**TDD steps:**

1. Add failing tests proving production routes preserve backend states, evidence links, reproducibility data, and `data_mode`.
2. Require canonical IDs and confirmed revision IDs; never silently store unresolved strings as verified targets.
3. Add provenance constraints so sample results cannot populate verified evaluation/recommendation tables.
4. Persist scenario inputs and backend result IDs/hashes, not independently recreated academic conclusions.
5. Keep the demo functional and visibly labeled when the production backend is not configured.

## Task 9: End-to-end fixture and complete verification

1. Add an offline fixture walkthrough: Bellevue transcript -> review -> confirmed revision -> UW guide resolution -> two UW Seattle majors -> separate general/major results -> transfer-term plan -> evidence drill-down.
2. Assert every positive academic conclusion resolves to exact evidence in its named snapshot.
3. Assert every unknown/deferred item stays labeled and is not promoted by the UI.
4. Run:

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m pytest
npm run typecheck
npm run lint
npm run build
docker compose up -d postgres
python -m alembic upgrade head
python -m alembic check
```

5. Also run the standalone recommendation-service suite if any of its retained code changes; its dependencies are not covered by the root Python baseline.
6. Obtain an independent final code review focused on evidence integrity, append-only behavior, PII/auth boundaries, campus scoping, `not_found`, effective periods, unknown propagation, and sample/verified separation.
7. Document verified, unknown, and deferred capabilities in the final pull request. Do not claim live institutional coverage from fixtures.

## Suggested slice discipline

- Use one fresh implementation agent per task and an independent reviewer before moving to the next task.
- Start each behavior change with a failing test and capture the expected failure.
- Keep commits limited to one task; never stage unrelated files.
- Rebase or merge only inside `andrew`; never reset, force-push, or edit `main`.
- If a source or policy cannot be verified, implement the typed unavailable/unknown state and continue with offline fixtures rather than guessing.
