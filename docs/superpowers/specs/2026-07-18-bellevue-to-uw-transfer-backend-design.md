# Bellevue College to UW Seattle Transfer Backend Design

**Date:** 2026-07-18
**Status:** Approved design
**Source institution:** Bellevue College
**Destination:** University of Washington, Seattle campus

## Objective

Implement an evidence-backed backend that accepts a Bellevue College transcript, identifies published Bellevue-to-UW Seattle transfer outcomes, evaluates requirements for one or more selected UW Seattle majors, identifies missing or unresolved requirements, and builds an actionable plan toward the student's intended transfer term.

The product remains institution-neutral. This is the first complete source-to-destination pathway, not a Bellevue- or UW-themed rewrite.

## Student flow

1. The student uploads a Bellevue College transcript or enters Bellevue courses manually.
2. The backend parses and normalizes the record.
3. The student reviews uncertain, missing, repeated, transferred, or in-progress entries.
4. The student selects UW Seattle and one or more supported majors.
5. The backend resolves published transfer outcomes and evaluates general transfer and major requirements separately.
6. The backend returns completed, in-progress, missing, recommended, unknown, conflicting, and confirmation-required items.
7. The backend creates an evidence-backed plan based on the intended transfer term and preferred load.

Parsing and review happen before requirement evaluation so corrections cannot silently invalidate prior conclusions.

## Backend boundaries

### Source acquisition

Fetch only approved public official sources needed for this pathway:

- UW Bellevue-specific Equivalency Guide content
- UW Seattle course catalog and prerequisites
- UW transfer-admission and transfer-credit policies
- UW Seattle major classifications and requirements
- UW exam-credit policies when the transcript includes exam credit

All acquisition must use the existing safe fetch boundary, robots enforcement, domain/path allowlists, rate limits, response limits, canonical URLs, immutable snapshots, and conditional revalidation. Do not use authenticated or NetID content.

### Bellevue equivalency ingestion

Add deterministic extraction for Bellevue College records in the official UW Equivalency Guide. Preserve:

- Bellevue course or course sequence
- UW course, sequence, elective/general credit, or other published outcome
- Source and destination credits when stated
- One-to-one, one-to-many, many-to-one, sequence, alternative, and conditional mappings
- Minimum grades, restrictions, exclusions, duplicate-credit rules, notes, warnings, footnotes, and effective periods
- Explicit no-credit language
- Exact structured table cells or excerpts as evidence

Missing guide entries produce `not_found`, not `explicit_no_credit`. Ambiguous, conflicting, or structurally unsupported rows create review tasks and do not publish a confident mapping.

### Searchable course catalogs

Provide paginated, normalized, case-insensitive search endpoints for:

- UW Seattle courses used by the destination-course dropdown
- Bellevue College courses used for transcript correction and planning

Each result includes a stable identifier, institution, campus where applicable, subject, number, title, credits, effective period, and evidence status. UW and Bellevue records must never share ambiguous identifiers.

The UI may search by code or title, but the backend remains authoritative. Search must not fabricate a course when no record exists.

### Transcript reconciliation

The transcript pipeline must:

- Confirm the source institution is Bellevue College or require explicit correction
- Preserve raw extracted values alongside normalized values
- Parse course code, title, term, credits, grade, status, and source institution
- Support repeated, withdrawn, failed, pass/fail, transferred-in, and in-progress courses
- Avoid double-counting credits already transferred onto the Bellevue transcript
- Represent low-confidence fields as review items
- Support manual correction and addition through Bellevue course search
- Recompute analysis only from the confirmed transcript revision

### Transfer outcome resolution

For each confirmed Bellevue course, return exactly one high-level state while preserving all detailed outcomes:

- `direct_equivalent`
- `course_sequence_equivalent`
- `elective_or_general_credit`
- `transferable_no_direct_equivalent`
- `explicit_no_credit`
- `not_found`
- `conflicting_evidence`
- `manual_review_required`
- `cannot_determine`

Course equivalency, transferable credits, degree applicability, and major applicability remain separate properties. A Bellevue course can award UW credit without satisfying a selected major requirement.

### Multi-major requirement evaluation

The student may select multiple UW Seattle majors. Evaluate:

- General UW transfer-admission requirements
- Each major's admission requirements independently
- Required versus recommended preparation
- AND, OR, CHOOSE-N, sequences, concurrent requirements, minimum grades, GPA or credit thresholds, restrictions, and unresolved fragments
- Requirements shared across selected majors
- Requirements unique to one major
- Whether a Bellevue course satisfies a requirement only through a published mapping

Do not produce admission probabilities. Return evidence-backed readiness states such as ready based on published requirements, ready after current coursework, missing verified requirements, preparation recommended, manual confirmation required, and insufficient evidence.

### Transfer-term planning

Planning inputs include intended transfer term, current/in-progress term, preferred credits per term, and whether summer attendance is allowed.

The planner may recommend a Bellevue course only when:

1. The selected major or UW transfer requirement is supported by published evidence.
2. A published Bellevue-to-UW mapping supports the course's destination outcome, or the recommendation is explicitly labeled as requiring confirmation.
3. Prerequisite ordering and minimum-grade logic are preserved.
4. The course does not create duplicate credit according to published evidence.

Each recommendation explains the requirement served, selected majors supported, published UW outcome, prerequisite effect, timing rationale, confidence, and evidence. Do not claim that Bellevue will offer a course in a particular term unless verified schedule data is ingested separately.

## Required API capabilities

Define typed request and response contracts for:

- Institution and pathway capability lookup
- UW and Bellevue course search
- Bellevue transcript upload, parsing status, review items, corrections, and confirmed revisions
- UW Seattle program search and detail
- Bellevue-to-UW transfer outcome lookup
- Multi-major requirement analysis
- Transfer-term plan generation
- Evidence detail, conflicts, and review tasks

Long-running transcript or ingestion work uses explicit job states. Analysis responses identify the transcript revision, selected program versions, evidence snapshot versions, and generation time so results are reproducible.

## Publication and evidence rules

- Every published mapping, requirement, readiness conclusion, and recommendation resolves to exact evidence in named snapshots.
- Calculations cite the evidence-backed inputs and identify the deterministic rule used.
- Model output cannot create or upgrade an equivalency.
- Historical evidence and record versions remain append-only.
- Stale or conflicting evidence blocks affected publication or produces a visible non-confident state.
- Network and OpenAI calls remain opt-in and dependency-injected in tests.
- Raw page bodies and source-containing model prompts are never logged.

## Acceptance criteria

- A verified Bellevue transcript can be parsed, reviewed, corrected, and confirmed.
- UW Seattle and Bellevue courses are searchable by code and title through backend APIs.
- At least representative direct, sequence, elective/general, explicit-no-credit, not-found, and manual-review outcomes are covered by deterministic fixtures and tests.
- Missing equivalency data is never reported as no credit.
- One analysis request can evaluate multiple UW Seattle majors without mixing their requirements.
- General transfer readiness and major readiness are separate.
- Every completed or missing requirement explains how it was evaluated and exposes exact evidence.
- Plans recommend Bellevue courses rather than UW courses when describing pre-transfer work, while showing the published UW outcome.
- The intended transfer term constrains prerequisite sequencing without inventing course availability.
- UW Bothell and Tacoma data cannot enter the Seattle pathway.
- Offline tests use fixtures and dependency injection; no test requires live network or OpenAI access.
- All repository quality gates pass.

## Implementation mega prompt

```text
You are the lead backend engineer for Pathwise, an institution-neutral transfer-planning platform. Implement the first complete evidence-backed transfer pathway: Bellevue College to the University of Washington, Seattle campus.

Read AGENTS.md first and follow it exactly. Inspect the current branch, git status, recent commits, architecture documents, Python ingestion pipeline, database and Alembic models, FastAPI routes, transcript pipeline, UW adapters, evidence validation, prerequisite evaluator, publishing gates, fixtures, and tests before changing anything. Preserve unrelated user work.

GOAL

Build the backend needed for this student journey:

1. Upload a Bellevue College transcript or enter Bellevue courses manually.
2. Parse the transcript and require review of missing or uncertain data.
3. Select UW Seattle and one or more supported majors.
4. Resolve what each Bellevue course transfers to at UW using official published evidence.
5. Evaluate general UW transfer requirements and each selected major's requirements independently.
6. Show completed, in-progress, missing, recommended, unknown, conflicting, and confirmation-required requirements.
7. Create an evidence-backed pre-transfer course plan based on the intended transfer term and preferred load.

SCOPE

- Source institution: Bellevue College only.
- Destination institution: University of Washington, Seattle campus only.
- Keep Pathwise and all shared contracts institution-neutral so future pathways can be added without redesigning the backend.
- Do not add verified support for other institutions or UW campuses in this iteration.

SOURCE INGESTION

- Use the existing safe acquisition boundary to fetch only approved public official UW sources.
- Add deterministic ingestion for Bellevue College entries in the official UW Equivalency Guide.
- Continue ingesting UW Seattle courses, prerequisites, transfer policies, major classifications, major requirements, and applicable exam-credit policies.
- Respect robots, allowlists, rate limits, response-size limits, conditional caching, canonical URLs, and immutable snapshots.
- Do not access authenticated or NetID content.
- Inspect the live source structure only through opt-in source-inspection tooling. Persist no inferred claim until deterministic fixtures and evidence validation support it.

EQUIVALENCY DATA MODEL AND PARSER

- Inspect the current schema before adding tables. Reuse versioned record and evidence infrastructure where appropriate; use Alembic for necessary PostgreSQL changes.
- Represent Bellevue source course(s), UW destination outcome(s), credits, mapping type, restrictions, minimum grades, notes, footnotes, warnings, duplicate-credit rules, effective period, campus, and exact evidence.
- Preserve one-to-one, one-to-many, many-to-one, sequence, alternative, and conditional mappings.
- Support these explicit resolution states:
  direct_equivalent,
  course_sequence_equivalent,
  elective_or_general_credit,
  transferable_no_direct_equivalent,
  explicit_no_credit,
  not_found,
  conflicting_evidence,
  manual_review_required,
  cannot_determine.
- Never infer no credit from absence. Only exact official no-credit language may produce explicit_no_credit.
- Ambiguous or conflicting rows create review tasks and block confident publication.
- Every published mapping must resolve to exact structured table cells or excerpts in its named immutable snapshot.

COURSE SEARCH

- Implement paginated, normalized, case-insensitive backend search for UW Seattle courses and Bellevue courses.
- Support code and title queries suitable for searchable dropdowns.
- Return stable IDs, institution ID, campus where applicable, subject, number, display code, title, credits, effective period, and evidence/publication state.
- Provide exact-detail endpoints with evidence and version information.
- Do not fabricate records or let the client submit arbitrary course identifiers as verified courses.
- Use institution-qualified canonical keys so Bellevue and UW course identifiers cannot collide.

TRANSCRIPT PIPELINE

- Accept PDF upload through the existing transcript pipeline and support manual course entry.
- Confirm or explicitly correct the source institution as Bellevue College.
- Preserve raw extraction alongside normalized fields.
- Parse institution, course code, title, term, credits, grade, and status.
- Support repeats, withdrawals, failures, pass/fail, transferred-in credit, and in-progress work.
- Detect possible double counting of transfer entries already represented by Bellevue coursework.
- Create review items for low-confidence or missing fields.
- Allow corrections and manual additions using Bellevue course IDs from the searchable catalog.
- Version confirmed transcript revisions. Requirement analysis must reference one confirmed revision and rerun after correction.
- Keep model calls opt-in and dependency-injected. Do not log raw transcript contents or full prompts.

PROGRAM AND REQUIREMENT ANALYSIS

- Expose searchable UW Seattle programs and program details from published, evidence-backed records.
- Accept multiple selected UW Seattle major IDs in one analysis request.
- Evaluate general UW transfer-admission requirements separately from each major's admission requirements.
- Preserve required versus recommended preparation, AND/OR/CHOOSE-N grouping, sequences, concurrency, minimum grades, credit and GPA thresholds, restrictions, footnotes, effective dates, warnings, and unresolved fragments.
- Map confirmed Bellevue coursework through published equivalencies before evaluating UW course requirements.
- Do not treat a UW credit award as automatic degree or major applicability.
- Return shared requirements across selected majors and major-specific requirements without merging their logical trees.
- Use descriptive readiness states, not probabilities or arbitrary percentages.
- Every evaluation result must include reasons, deterministic rule identifiers, source record versions, and exact evidence references.

PLANNING

- Generate a pre-transfer plan using intended transfer term, current term, preferred credits per term, summer preference, confirmed Bellevue record, selected UW majors, verified equivalencies, and prerequisite graphs.
- Recommend Bellevue courses as the actions the student can take before transfer. Show their published UW outcomes alongside them.
- Recommend a course only when evidence supports the target requirement and mapping. If confirmation is needed, label it and do not present it as satisfied.
- Prioritize missing required courses, prerequisite bottlenecks, courses shared by multiple selected majors, and time-sensitive preparation.
- Respect course sequences, minimum grades, duplicate-credit rules, and maximum load.
- Explain why each course is recommended, what it satisfies, what it unlocks, which majors it supports, and the exact evidence.
- Do not assert Bellevue term availability unless a separately verified Bellevue schedule source is implemented. Label proposed terms as planning slots, not confirmed offerings.
- Return infeasible, unresolved, and confirmation-required states instead of inventing a valid plan.

API CONTRACTS

Implement typed FastAPI contracts and routes, following existing conventions, for:

- Pathway/institution capabilities
- Bellevue and UW course search/detail
- Transcript upload and parse-job status
- Transcript review items, corrections, confirmation, and revisions
- UW Seattle program search/detail
- Bellevue-to-UW transfer-outcome lookup
- Multi-major requirement analysis
- Transfer-term plan generation
- Evidence, conflicts, and review tasks

Responses must include the confirmed transcript revision, record versions, evidence snapshot identifiers, effective dates, campus scope, and generation time. Use explicit job states for long-running work. Add pagination and safe query limits.

TEST-DRIVEN DELIVERY

- Before each behavior change, add a failing test and confirm it fails for the intended reason.
- Use deterministic Bellevue/UW HTML and transcript fixtures for offline tests.
- Add parser tests for direct, sequence, alternative, conditional, elective/general, explicit-no-credit, not-found, malformed, conflicting, and changed-source cases.
- Add integration tests proving that every published mapping and requirement result has exact evidence in the correct snapshot.
- Add transcript tests for corrections, repeats, transfer-entry double counting, in-progress courses, and confirmed revision invalidation.
- Add multi-major tests for shared requirements, distinct requirement trees, minimum grades, unknown mappings, and contradictory sources.
- Add planning tests for prerequisite ordering, transfer deadline constraints, shared-major optimization, max load, summer preference, duplicate credit, infeasible timelines, and unverified course availability.
- Add API tests for pagination, search normalization, campus isolation, unsupported institutions, stale versions, invalid IDs, and reproducibility metadata.
- Network and OpenAI calls must be disabled by default and dependency-injected in tests.

IMPLEMENTATION PROCESS

1. Audit and document the current schema, APIs, incomplete Equivalency Guide adapter, transcript pipeline, and reusable evidence infrastructure.
2. Produce a staged implementation plan with exact files, migrations, contracts, test cases, and commit boundaries before production changes.
3. Implement vertical slices in this order:
   a. canonical institution/pathway capabilities and course search,
   b. Bellevue equivalency extraction and versioned persistence,
   c. transcript reconciliation and confirmed revisions,
   d. multi-major requirement evaluation,
   e. transfer-term planning,
   f. complete API and evidence integration.
4. Run narrow tests after each red-green cycle and the full quality gate at each milestone.
5. Do not silently replace verified backend behavior with existing mock frontend analysis.

REQUIRED VERIFICATION

python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m pytest
npm run typecheck
npm run lint
npm run build

For schema or persistence changes:

docker compose up -d postgres
python -m alembic upgrade head
python -m alembic check

FINAL ACCEPTANCE

- A Bellevue transcript can be uploaded, reviewed, corrected, confirmed, and analyzed.
- Bellevue and UW Seattle courses are searchable for UI dropdowns.
- Published Bellevue-to-UW outcomes are evidence-backed and versioned.
- Missing guide entries never become no credit.
- Multiple UW Seattle majors can be evaluated in one analysis without corrupting logical grouping.
- General transfer and major readiness remain separate.
- Missing requirements and recommended Bellevue courses are explained with exact evidence.
- The plan responds to transfer term and course-load constraints without inventing Bellevue availability.
- Seattle scope is explicit and Bothell/Tacoma data cannot leak in.
- No synthetic fixture or model output is presented as verified guidance.
- The architecture remains institution-neutral and extendable to another source/destination pathway.

At completion, perform a reproducible end-to-end fixture walkthrough and report exactly which conclusions are verified, which remain unknown, and which features are deliberately deferred. Do not claim production readiness solely because tests pass.
```

## Deferred

- Source colleges other than Bellevue College
- Destinations other than UW Seattle
- UW Bothell and Tacoma
- Unpublished course-equivalency inference
- Admission probability prediction
- Confirmed Bellevue course scheduling unless an official schedule adapter is separately designed
- Automatic registration or advising decisions
