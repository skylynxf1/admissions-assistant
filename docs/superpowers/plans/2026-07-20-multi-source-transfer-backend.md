# Multi-Source Transfer Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the transfer-analysis pipeline real end-to-end for two source institutions — Bellevue College *and* Seattle University → UW Seattle — by publishing evidence-backed academic data into the Supabase application schemas and resolving transfer outcomes deterministically from that data, replacing mock analysis.

**Architecture:** The Python/FastAPI `academic_ingest` service stays the sole authority for public academic facts and evidence. A new **publisher** moves *approved* ingestion records into the Supabase application schemas (`catalog`, `policy`, `equivalency`). The **recommendation service** (`services/course-recommendation`, already Supabase-aware) and the Next.js app read only from those published schemas. Everything is institution-neutral: adding Seattle University is data + config, not new engine code.

**Tech Stack:** Python 3.12, Pydantic v2, FastAPI, async SQLAlchemy 2, Alembic/PostgreSQL, Supabase (PostgREST), Next.js/TypeScript, pytest, Ruff, mypy, Vitest.

## Global Constraints

- Branch: work on `andrew`. Do **not** modify `main`. Do not commit on the author's behalf — the author commits.
- Source institutions this iteration: **Bellevue College** and **Seattle University** only. Destination: **UW Seattle** only. Reject UW Bothell/Tacoma identifiers before evaluation.
- Transfer-state vocabulary is the spec's 9 states exactly: `direct_equivalent`, `course_sequence_equivalent`, `elective_or_general_credit`, `transferable_no_direct_equivalent`, `explicit_no_credit`, `not_found`, `conflicting_evidence`, `manual_review_required`, `cannot_determine`.
- A missing equivalency lookup is `not_found`, **never** `explicit_no_credit`. Only exact official no-credit language produces `explicit_no_credit`.
- Every published mapping/requirement/readiness result resolves to exact evidence in a named snapshot. Model output cannot create or upgrade an equivalency.
- Historical source/record/analysis versions are append-only.
- Network and OpenAI calls are opt-in and dependency-injected. Offline tests use fixtures; no test requires live network or OpenAI.
- Never log credentials, raw page bodies, student documents, or full prompts containing source content.
- Verification gate at each milestone: `python -m ruff check .`, `python -m ruff format --check .`, `python -m mypy src`, `python -m pytest`, and for the frontend `npm run typecheck && npm run lint && npm run build`.
- Baseline before starting: Python `122 passed`, frontend `4 passed`.

---

## Demo scope vs full plan

This plan covers **all seven features** from the "needs more work" table. It is layered so you can stop at any phase with working software.

- **Tomorrow's demo slice (achievable tonight):** Phase 0 + Phase 2 (curated verified mappings, loaded directly into the existing Supabase `equivalency` schema — bypassing the heavy publisher) + Phase 3a (deterministic transfer-outcome resolver) + a FastAPI endpoint. This demonstrates Bellevue→UW **and** Seattle U→UW through one engine, evidence-cited, provable via Swagger/curl — no UI required.
- **Full integration (Phases 1, 3b, 4–8):** the correct, durable path — the publisher bridge, multi-major evaluation, service/frontend wiring, advisor grounding, live transcript parsing, and auth. This is multi-day work; do not promise it for the demo.

Feature-table coverage map:

| Table feature | Phase(s) |
|---|---|
| Bellevue-to-UW coverage (+ Seattle U) | 0, 2, 3 |
| Evidence publication (the publisher) | 1 |
| Course recommendations (wire the service) | 4 |
| Academic analysis & simulation (de-mock) | 3, 5 |
| AI advisor (ground in evidence) | 6 |
| Live transcript parsing (Docling + OpenAI) | 7 |
| Supabase persistence (sign-in/session) | 8 (partner-owned UI) |

---

## File Structure

New/changed units (responsibility in parens):

- `config/institutions/bellevue_college.yaml`, `config/institutions/seattle_university.yaml` (source institution configs; mirror `uw_seattle.yaml`)
- `config/pathways/pathways.yaml` (pathway registry: source→destination + capabilities)
- `src/academic_ingest/pathways/registry.py` (typed pathway lookup)
- `src/academic_ingest/models/transfer_state.py` (the single 9-state enum + mapping helpers)
- `src/academic_ingest/validation/source_scope.py` (generalize from hard-coded UW to injected allowlists)
- `src/academic_ingest/adapters/bellevue/equivalency_guide.py`, `src/academic_ingest/adapters/seattle_university/equivalency_guide.py` (parse each source's rows from the UW Equivalency Guide; created only after the public source policy is confirmed)
- `src/academic_ingest/publishing/supabase_publisher.py` (move approved records → Supabase app schemas)
- `src/academic_ingest/transfer/resolver.py` (deterministic per-course transfer-outcome resolver)
- `src/academic_ingest/api/routes/transfer.py` (typed FastAPI transfer endpoints)
- `supabase/seed_equivalencies/*.sql` **or** a fixtures module (curated verified mappings for the demo slice)
- `tests/transfer/`, `tests/publishing/`, `tests/pathways/`, `tests/fixtures/bellevue/`, `tests/fixtures/seattle_university/`

---

## Phase 0 — Foundations (demo-critical)

### Task 0.1: Single transfer-state vocabulary

**Files:**
- Create: `src/academic_ingest/models/transfer_state.py`
- Test: `tests/transfer/test_transfer_state.py`
- Reference (do not fabricate — read first): `src/academic_ingest/models/enums.py`, `supabase/migrations/202607160001_initial_backend.sql:391-409` (the `equivalency.mapping_type` enum, which currently uses `no_credit`, not `explicit_no_credit`)

**Interfaces:**
- Produces: `class TransferState(str, Enum)` with the 9 members named exactly per Global Constraints; `SUPABASE_MAPPING_TYPE_TO_STATE: dict[str, TransferState]` and `STATE_TO_SUPABASE_MAPPING_TYPE: dict[TransferState, str]` bridging the DB enum spelling (`no_credit` ↔ `explicit_no_credit`, `elective` ↔ `elective_or_general_credit`, etc.).

- [ ] **Step 1:** Write `tests/transfer/test_transfer_state.py` asserting all 9 members exist, that `SUPABASE_MAPPING_TYPE_TO_STATE["no_credit"] is TransferState.explicit_no_credit`, and that the two dicts are inverse where defined.
- [ ] **Step 2:** Run `python -m pytest tests/transfer/test_transfer_state.py -v` — expect FAIL (module missing).
- [ ] **Step 3:** Implement `transfer_state.py` with the enum and the two bridging dicts (read the DB enum values from the migration first and map every one).
- [ ] **Step 4:** Run the test — expect PASS.
- [ ] **Step 5:** `python -m ruff check src tests && python -m mypy src`. Stop for the author to commit.

### Task 0.2: Source-scope generalization (institution-injected allowlists)

**Files:**
- Modify: `src/academic_ingest/validation/source_scope.py` (currently hard-codes `washington.edu`/`seattle` — lines 9-39)
- Create: `config/institutions/bellevue_college.yaml`, `config/institutions/seattle_university.yaml` (mirror `config/institutions/uw_seattle.yaml`: `institution_id`, `allowed_domains`, `disallowed_campus_patterns`, `request_policy`)
- Test: `tests/validation/test_source_scope.py`

**Interfaces:**
- Produces: `validate_source_scope(url: str, campus: str, *, allowed_hosts: set[str], destination_campus: str, disallowed_campus_patterns: set[str]) -> list[ValidationIssue]`. The UW Seattle destination guard (reject `bothell`/`tacoma`) is preserved by passing UW's config; the function itself is institution-neutral.

- [ ] **Step 1:** Write failing tests: (a) a Bellevue equivalency-guide URL on `washington.edu` passes the source-host check when UW hosts are allowed (the Equivalency Guide is a UW-hosted source describing Bellevue rows); (b) a `bothell` campus still returns `campus_out_of_scope`; (c) an arbitrary host returns `source_outside_official_scope`.
- [ ] **Step 2:** Run — expect FAIL (signature mismatch).
- [ ] **Step 3:** Refactor `validate_source_scope` to accept injected `allowed_hosts`/`disallowed_campus_patterns` instead of the hard-coded `is_official_uw_url`; keep a thin `uw_seattle_scope(...)` wrapper that supplies UW's config so existing callers don't break. Update callers.
- [ ] **Step 4:** Run the new tests **and** the full suite (`python -m pytest`) — expect PASS, no regressions.
- [ ] **Step 5:** Ruff + mypy. Stop for commit.

### Task 0.3: Pathway registry

**Files:**
- Create: `config/pathways/pathways.yaml` (entries `bellevue-college:uw-seattle`, `seattle-university:uw-seattle`, each naming source institution config, destination institution+campus, and enabled capabilities)
- Create: `src/academic_ingest/pathways/registry.py`
- Test: `tests/pathways/test_registry.py`

**Interfaces:**
- Produces: `@dataclass(frozen=True) class Pathway` (`key`, `source_institution_id`, `destination_institution_id`, `destination_campus`, `capabilities: frozenset[str]`); `load_pathways(path) -> dict[str, Pathway]`; `get_pathway(key) -> Pathway` raising `UnknownPathwayError` on miss.

- [ ] **Step 1:** Failing test: `get_pathway("bellevue-college:uw-seattle").destination_campus == "Seattle"`; unknown key raises; both pathways load.
- [ ] **Step 2:** Run — expect FAIL.
- [ ] **Step 3:** Implement the YAML + loader.
- [ ] **Step 4:** Run — expect PASS.
- [ ] **Step 5:** Ruff + mypy. Stop for commit.

---

## Phase 2 — Multi-source equivalency coverage (demo-critical)

> For the **demo slice**, implement Task 2.1 (curated verified mappings) and skip live parsing (2.2) — parsing needs the confirmed public source policy and is Phase-1-publisher territory.

### Task 2.1: Curated verified mappings for both pathways (demo data)

**Files:**
- Create: `supabase/seed_equivalencies/bellevue_uw.sql`, `supabase/seed_equivalencies/seattle_university_uw.sql` (INSERTs into `equivalency.course_equivalencies` + `equivalency.equivalency_components`, matching the schema at migration `202607160001_initial_backend.sql:391-427`; each row sets `source_institution_id`, `destination_institution_id`, `mapping_type`, `minimum_grade`, `conditions`, `confidence`, `review_status='verified'`)
- Create: `docs/equivalencies/SOURCES.md` (each mapping's exact UW Equivalency Guide citation — URL + retrieved date)
- Test: `tests/transfer/test_seed_equivalencies_shape.py` (parse the SQL / load into a test DB and assert every row cites a source and uses a valid `mapping_type`; assert at least one `not_found` and one no-credit exist per pathway)

**Content (real, cited):** curate ~12–15 mappings per source from the official UW Equivalency Guide, including a direct equivalent, a sequence, an elective/general-credit, a deliberate no-credit, and a `not_found` gap. Institutions already exist in `supabase/seed.sql` (Bellevue College `...004`, Seattle University `...005`, UW Seattle `...001`).

- [ ] **Step 1:** Write the shape test (fails: files missing).
- [ ] **Step 2:** Run — expect FAIL.
- [ ] **Step 3:** Author the two SQL files + `SOURCES.md` from the live Equivalency Guide (cite every row; label confidence honestly — `high` only where the guide is unambiguous).
- [ ] **Step 4:** Load into the cloud/local Supabase (`equivalency` schema) and run the shape test — expect PASS.
- [ ] **Step 5:** Ruff (Python test) + `SOURCES.md` review. Stop for commit.

### Task 2.2: Live Equivalency-Guide parsers *(post-demo)*

**Files:** `src/academic_ingest/adapters/bellevue/equivalency_guide.py`, `src/academic_ingest/adapters/seattle_university/equivalency_guide.py`; extend `src/academic_ingest/adapters/uw/equivalency_guide.py` (currently discovers/snapshots only — plan defect line 44). Deterministic table-cell extraction → typed mapping records with exact evidence. Fixture-driven tests for direct/sequence/alternative/conditional/elective/no-credit/not-found/malformed/conflicting cases. **Gated on** confirming the source's robots/allowlist policy first. Feeds Phase 1 publisher.

---

## Phase 3 — Transfer-outcome resolver & requirement evaluation

### Task 3a: Deterministic transfer-outcome resolver (demo-critical)

**Files:**
- Create: `src/academic_ingest/transfer/resolver.py`
- Create: `src/academic_ingest/api/routes/transfer.py` + register in `src/academic_ingest/api/app.py`
- Test: `tests/transfer/test_resolver.py`, `tests/api/test_transfer_routes.py`

**Interfaces:**
- Consumes: `TransferState` (Task 0.1); `get_pathway` (Task 0.3); equivalency rows from Supabase `equivalency.course_equivalencies` (or an injected repository returning them).
- Produces: `resolve_outcomes(pathway_key: str, source_courses: list[SourceCourseInput], repo: EquivalencyReadRepository) -> list[TransferOutcome]`, where `TransferOutcome` carries `source_course`, `state: TransferState`, `destination_outcomes`, `credits_awarded`, `minimum_grade`, `conditions`, `evidence_refs`. A course with no matching row resolves to `not_found` (never `explicit_no_credit`). Conflicting rows → `conflicting_evidence`. Ambiguous → `manual_review_required`.

- [ ] **Step 1:** Write resolver tests over a fixture repo: direct → `direct_equivalent`; two-course sequence → `course_sequence_equivalent`; unmapped course → `not_found`; explicit no-credit row → `explicit_no_credit`; two contradictory rows → `conflicting_evidence`. Run the **same** cases for both pathway keys to prove institution-neutrality.
- [ ] **Step 2:** Run — expect FAIL.
- [ ] **Step 3:** Implement `resolver.py` (pure function over injected repo; no I/O in the resolver).
- [ ] **Step 4:** Run resolver tests — expect PASS.
- [ ] **Step 5:** Add `POST /transfer/outcomes` route (typed request: `pathway_key`, `courses`; typed response includes resolver output + generation time + evidence snapshot ids). Add route tests incl. unknown pathway → 404 and Bothell/Tacoma rejection → 422.
- [ ] **Step 6:** Run `python -m pytest tests/transfer tests/api/test_transfer_routes.py` — expect PASS. Ruff + mypy. Stop for commit.

### Task 3b: Multi-major requirement evaluation *(post-demo)*

Evaluate general UW transfer-admission requirements separately from each selected major, preserving AND/OR/CHOOSE-N/sequence/concurrency/min-grade/thresholds, mapping confirmed source courses through published equivalencies before matching UW course requirements, returning descriptive readiness states (never probabilities), shared vs major-specific requirements without merging logical trees. Reads published `policy.requirements` + `policy.requirement_courses`. Extends the recommendation service's evaluation rather than duplicating it. Full TDD task set to be expanded when reached (depends on Phase 1 publishing real requirement trees).

---

## Phase 1 — Evidence publisher (ingestion → Supabase app schemas)

> The table's "Add the publisher that moves approved ingestion records into the Supabase application schemas." The durable replacement for Task 2.1's hand-loaded data. Large; **not** in the demo slice.

### Task 1.1: Publisher for courses, programs, requirements, equivalencies

**Files:**
- Create: `src/academic_ingest/publishing/supabase_publisher.py`
- Modify: `src/academic_ingest/publishing/service.py` (route publication through the gate; reference before editing — do not assume signatures)
- Test: `tests/publishing/test_supabase_publisher.py`

**Interfaces:**
- Produces: `publish_pathway(pathway_key, *, ingestion_repo, supabase_client, only_approved=True) -> PublishReport`. Writes append-only into `catalog.institutions/programs/recommendation_courses/course_offerings`, `policy.requirements/requirement_courses/course_prerequisite_groups/course_prerequisite_conditions/general_education_mappings`, `equivalency.course_equivalencies/equivalency_components/recommendation_course_equivalencies` — exactly the tables `SupabaseRecommendationRepository.load_dataset` reads (`services/course-recommendation/app/repository.py:88-207`). Only records with validated evidence and `review_status` approved are published; each carries its `source_ids`.

- [ ] TDD steps: failing test that (a) an unapproved record is not published, (b) a published equivalency row's `mapping_type` round-trips through `STATE_TO_SUPABASE_MAPPING_TYPE`, (c) re-publishing appends a new version rather than mutating history, (d) published rows satisfy `SupabaseRecommendationRepository`'s column expectations. Implement, verify, Alembic if ingestion-side schema changes, run full gate. Stop for commit.

---

## Phase 4 — Wire the recommendation service + Next.js proxy

### Task 4.1: Recommendation service in Supabase mode against published data
- Confirm `services/course-recommendation` `/health` reports `"mode":"supabase"` with `SUPABASE_URL`/`SUPABASE_SERVICE_ROLE_KEY` set (per `repository.py:78-86`). Add an integration test that `load_dataset` succeeds against a seeded test scenario referencing Bellevue courses + UW targets.

### Task 4.2: Next.js proxy + typed adapter (backend surface only; UI is partner-owned)
- Create `app/api/recommendations/route.ts` that proxies to `RECOMMENDATION_SERVICE_URL` (currently configured but uncalled) with a typed response adapter. Do not build UI; expose the typed endpoint so the partner's dashboard can consume it. Vitest for the adapter mapping.

---

## Phase 5 — Replace mock policy-analysis with evidence-backed records

- Swap `lib/services/index.ts` mock bindings (`MockScenarioSimulator`, `MockCourseRecommendationEngine`, `MockPolicyRetrievalService`, …) for adapters that call the recommendation service / read published Supabase records. Keep the mock implementations behind a feature flag so demos can still run offline. The analysis response must cite evidence and the deterministic rule used. Replace one service at a time, each with a failing contract test first.

---

## Phase 6 — Ground AI advisor in published evidence *(later)*

- `app/api/advisor/route.ts` currently calls `MockAdvisorChatService`. Wire the live OpenAI server implementation (dependency-injected, opt-in via `OPENAI_API_KEY`) and constrain answers to published evidence + the confirmed transcript revision only; every claim carries citation ids; refuse when evidence is absent. Never log full prompts containing source content. Offline test uses a fake client.

---

## Phase 7 — Live transcript parsing config *(ops/config)*

- Stand up the Docling worker (`services/transcript-parser`) and set `DOCLING_SERVICE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL` (all currently unset). With both configured, `POST /api/transcript/extract` processes the real PDF; otherwise it returns labeled sample extraction (existing behavior). No code change required beyond config + a smoke test; document in `docs/TRANSCRIPT_PIPELINE.md`.

---

## Phase 8 — Supabase persistence: sign-in/session *(partner-owned UI)*

- The server clients, RLS, and transcript/scenario routes exist. Remaining: a sign-in/session UI so plans save to accounts instead of local storage. This is **frontend** work owned by the partner; the backend dependency is only that `saveDraft` already posts to `/api/transcripts` + `/api/scenarios` with the session access token (`components/app-provider.tsx:162-199`). No backend task here beyond confirming those routes accept the authenticated session.

---

## Self-Review notes

- **Coverage:** every table feature maps to a phase (see map above). The two-source scalability requirement is satisfied by Tasks 0.3, 2.1, and 3a running identical logic over two pathway keys.
- **Vocabulary consistency:** all tasks use the single `TransferState` from Task 0.1; the DB-spelling bridge lives only there.
- **Honest gaps flagged inline:** Tasks 2.2, 3b, and Phase 1 are marked post-demo; the demo slice deliberately loads curated (cited) data directly rather than through the not-yet-built publisher.
- **Files referenced but unread by the author** (`publishing/service.py`, `db/models.py`) are called out as "reference/confirm before editing" rather than given fabricated signatures.
