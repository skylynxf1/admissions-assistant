# UW Seattle Academic Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a production-quality, evidence-preserving, institution-independent Python ingestion service with a bounded University of Washington Seattle adapter suite.

**Architecture:** Preserve the existing Next.js prototype and add a separate FastAPI service in `src/academic_ingest`. The service uses typed pipeline stages, immutable snapshots, deterministic adapters, evidence-gated publishing, PostgreSQL version history, conservative GPT fallback, and offline fixtures.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, PostgreSQL, Alembic, HTTPX, selectolax, OpenAI Python SDK, pytest, pytest-asyncio, respx, Ruff, mypy, Docker Compose.

## Global Constraints

- Use Python 3.12 through `C:/Users/andzh/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe` in this workspace.
- PostgreSQL is the authoritative production store; default tests must run offline without a live UW source or OpenAI credential.
- Network crawling is disabled by default and requires an explicit `--allow-network` flag plus `ACADEMIC_INGEST_CONTACT_EMAIL`.
- Only `https` URLs on configured official domains may be fetched; redirects are validated before following.
- Bothell and Tacoma records must never be published as Seattle records.
- Raw snapshots and evidence are immutable; version changes append records rather than mutating history.
- Exact evidence is mandatory for published prerequisites, requirements, admissions rules, transfer policies, and exam-credit rules.
- “Mapping not found” and “explicit no credit” are separate enum values and validation states.
- GPT output is advisory extraction only; deterministic code verifies evidence and assigns confidence.
- Time Schedule ingestion and Equivalency Guide support remain conditional on public access, robots permission, and stable structure.
- Preserve the existing Next.js mock experience and TypeScript contracts.

## File Map

- `pyproject.toml`, `alembic.ini`, `docker-compose.yml`: Python tooling and runtime services.
- `config/institutions/uw_seattle.yaml`: UW Seattle domain, seed, campus, policy, and request configuration.
- `src/academic_ingest/models/`: domain enums and Pydantic records.
- `src/academic_ingest/db/`: SQLAlchemy tables, sessions, repositories, and migrations.
- `src/academic_ingest/discovery/`, `fetching/`, `snapshots/`: safe acquisition boundary.
- `src/academic_ingest/classification/`, `adapters/`: deterministic page routing and extraction.
- `src/academic_ingest/prerequisites/`: recursive requirement AST, parser, renderer, evaluator.
- `src/academic_ingest/extraction/`: strict fake and OpenAI structured-extraction clients.
- `src/academic_ingest/validation/`, `conflicts/`, `confidence/`, `review/`, `publishing/`: publish gate and uncertainty handling.
- `src/academic_ingest/jobs/`: page-isolated pipeline orchestration and crawl-job summaries.
- `src/academic_ingest/api/`: FastAPI application, dependencies, schemas, and routes.
- `tests/fixtures/uw/`: concise synthetic UW-structure fixtures and expected JSON.
- `tests/unit/`, `tests/integration/`: offline behavior and end-to-end fixture tests.
- `scripts/`: bounded inspection, sample ingestion, and evidence-preserving export.
- `docs/`: source map, adapter notes, model, pipeline, extension, safety, and contributor guidance.

---

### Task 1: Python project scaffold and canonical product documents

**Files:**
- Create: `pyproject.toml`
- Create: `src/academic_ingest/__init__.py`
- Create: `tests/conftest.py`
- Create: `docker-compose.yml`
- Modify: `.env.example`
- Move: `gpt56_academic_planning_os_build_spec.md` to `docs/gpt56_academic_planning_os_build_spec.md`
- Move: `academic_planning_data_scraping_spec.pdf` to `docs/academic_planning_data_scraping_spec.pdf`
- Test: `tests/unit/test_package.py`

**Interfaces:**
- Produces: importable `academic_ingest` package with `__version__ = "0.1.0"`.
- Produces: pytest markers `integration` and `postgres` and a `tmp_path`-based offline environment fixture.

- [ ] **Step 1: Write the package smoke test**

```python
def test_package_exposes_version() -> None:
    import academic_ingest

    assert academic_ingest.__version__ == "0.1.0"
```

- [ ] **Step 2: Run the test and observe the missing-package failure**

Run: `python -m pytest tests/unit/test_package.py -q`
Expected: collection fails with `ModuleNotFoundError: No module named 'academic_ingest'`.

- [ ] **Step 3: Add the package and tooling configuration**

Use a `src` package layout. Configure Ruff for Python 3.12 with 100-character lines, mypy strict mode for `src`, pytest offline defaults, and dependencies for FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL, HTTPX, selectolax, Trafilatura, Docling, PyYAML, structlog, OpenAI, pytest, pytest-asyncio, respx, aiosqlite, Ruff, and mypy. Configure Docker Compose with PostgreSQL 16, a health check, and no hard-coded secret outside local-only defaults.

- [ ] **Step 4: Verify imports and existing frontend checks**

Run: `python -m pytest tests/unit/test_package.py -q`
Expected: `1 passed`.

Run: `npm run typecheck`
Expected: exit 0.

- [ ] **Step 5: Commit the scaffold**

```text
git add pyproject.toml docker-compose.yml .env.example src tests docs
git commit -m "build: scaffold academic ingestion service"
```

### Task 2: Inspect official UW sources and record access findings

**Files:**
- Create: `docs/uw-source-map.md`
- Create: `tests/fixtures/uw/source-inspection.json`

**Interfaces:**
- Produces: `InspectionResult(url, final_url, canonical_url, content_type, robots_allowed, adapter, policy_family, discovered_links, warnings)`.
- Produces: a checked-in inspection fixture consumed by the safe inspection script implemented in Task 14.

- [ ] **Step 1: Inspect only the specified official pages**

Check `robots.txt`, sitemap locations, canonical tags, content types, static HTML, embedded structured data, and stable selectors for `www.washington.edu` and `admit.washington.edu`. Do not recursively crawl, authenticate, bypass controls, or persist policy records.

- [ ] **Step 2: Record machine-readable inspection findings**

Store URL, final URL, canonical URL, content type, robots decision, adapter, policy family, discovered links, warnings, inspection timestamp, and HTTP status in `tests/fixtures/uw/source-inspection.json`.

- [ ] **Step 3: Document the source map**

Record the inspection timestamp, status, robots result, authority, campus scope, effective-date signals, adapters, dependencies, and limitations in `docs/uw-source-map.md`. Label inferences and inaccessible sources explicitly.

- [ ] **Step 4: Verify every required seed appears once**

Run: `python -m json.tool tests/fixtures/uw/source-inspection.json`
Expected: valid JSON containing each configured seed URL and both inspected hosts.

- [ ] **Step 5: Commit source findings**

```text
git add docs/uw-source-map.md tests/fixtures/uw/source-inspection.json
git commit -m "docs: map official UW ingestion sources"
```

### Task 3: Institution configuration and typed domain models

**Files:**
- Create: `config/institutions/uw_seattle.yaml`
- Create: `src/academic_ingest/config/settings.py`
- Create: `src/academic_ingest/models/enums.py`
- Create: `src/academic_ingest/models/domain.py`
- Create: `src/academic_ingest/models/__init__.py`
- Create: `src/academic_ingest/normalization/identifiers.py`
- Create: `src/academic_ingest/normalization/courses.py`
- Create: `src/academic_ingest/normalization/programs.py`
- Create: `src/academic_ingest/normalization/requirements.py`
- Create: `src/academic_ingest/normalization/terms.py`
- Test: `tests/unit/test_config.py`
- Test: `tests/unit/test_domain_models.py`
- Test: `tests/unit/test_normalization.py`

**Interfaces:**
- Produces: `InstitutionConfig`, `RequestPolicy`, and `load_institution_config(path: Path) -> InstitutionConfig`.
- Produces: all request-specified Pydantic domain records and `PipelineResult`.
- Produces: `MappingOutcome.NOT_FOUND` and `MappingOutcome.EXPLICIT_NO_CREDIT` as distinct values.
- Produces: canonical institution, campus, subject, course, program, term, and requirement identifiers while preserving source text.

- [ ] **Step 1: Write failing configuration and semantic-distinction tests**

```python
def test_uw_config_rejects_tacoma_scope(uw_config: InstitutionConfig) -> None:
    assert uw_config.institution_id == "uw-seattle"
    assert uw_config.campus == "Seattle"
    assert uw_config.url_belongs_to_disallowed_campus("https://tacoma.uw.edu/catalog")


def test_not_found_is_not_no_credit() -> None:
    assert MappingOutcome.NOT_FOUND is not MappingOutcome.EXPLICIT_NO_CREDIT
```

- [ ] **Step 2: Run focused tests and observe missing models**

Run: `python -m pytest tests/unit/test_config.py tests/unit/test_domain_models.py tests/unit/test_normalization.py -q`
Expected: import failures for the missing configuration and model modules.

- [ ] **Step 3: Implement strict Pydantic models and validators**

Use UUID identifiers, timezone-aware datetimes, Decimal credits, explicit effective periods, evidence identifiers, warnings, unresolved fields, authority/confidence/review enums, and immutable snapshot models. Reject negative credits and invalid effective ranges in Pydantic validation.

- [ ] **Step 4: Run model tests**

Run: `python -m pytest tests/unit/test_config.py tests/unit/test_domain_models.py tests/unit/test_normalization.py -q`
Expected: all tests pass.

- [ ] **Step 5: Commit configuration and domain models**

```text
git add config src/academic_ingest/config src/academic_ingest/models src/academic_ingest/normalization tests/unit
git commit -m "feat: define ingestion configuration and domain models"
```

### Task 4: SQLAlchemy persistence, Alembic migration, and version repositories

**Files:**
- Create: `src/academic_ingest/db/base.py`
- Create: `src/academic_ingest/db/models.py`
- Create: `src/academic_ingest/db/session.py`
- Create: `src/academic_ingest/db/repositories.py`
- Create: `src/academic_ingest/db/__init__.py`
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/versions/20260716_0001_initial_ingestion_schema.py`
- Test: `tests/integration/test_versioned_repository.py`
- Test: `tests/integration/test_idempotent_snapshots.py`

**Interfaces:**
- Produces: `DatabaseSettings`, `create_engine_and_session(settings)`, and transactional session dependency.
- Produces: `SourceRepository.upsert_page`, `create_snapshot`, `list_versions`, and `publish_version`.
- Produces: current-record queries that preserve superseded rows.
- Produces: `compute_changed_blocks(previous: bytes, current: bytes) -> list[ChangedBlock]` and material-change review routing.

- [ ] **Step 1: Write repository tests for idempotency and source changes**

```python
async def test_changed_snapshot_preserves_previous_version(repository, source_page) -> None:
    first = await repository.create_snapshot(source_page.id, b"first", crawl_job_id="job-1")
    second = await repository.create_snapshot(source_page.id, b"second", crawl_job_id="job-2")

    assert first.id != second.id
    assert [item.raw_content_hash for item in await repository.list_snapshots(source_page.id)] == [
        first.raw_content_hash,
        second.raw_content_hash,
    ]
```

- [ ] **Step 2: Run repository tests and observe missing persistence**

Run: `python -m pytest tests/integration/test_versioned_repository.py tests/integration/test_idempotent_snapshots.py -q`
Expected: import failures for `academic_ingest.db`.

- [ ] **Step 3: Implement normalized persistence and initial migration**

Map every core domain entity to SQLAlchemy 2 declarative tables. Use foreign keys for evidence, expressions, versions, conflicts, and review tasks. Use JSON only for metadata, conditions, warnings, parser metrics, response headers, and explainable confidence factors. Add unique constraints for canonical source identity, snapshot hash observations, canonical course versions, and idempotent publication keys.

- [ ] **Step 4: Verify repository tests and migration syntax**

Run: `python -m pytest tests/integration/test_versioned_repository.py tests/integration/test_idempotent_snapshots.py -q`
Expected: all tests pass offline.

Run: `python -m alembic check`
Expected: no new upgrade operations detected after applying the migration in the test schema.

- [ ] **Step 5: Commit persistence**

```text
git add src/academic_ingest/db alembic.ini alembic tests/integration
git commit -m "feat: add versioned ingestion persistence"
```

### Task 5: Safe discovery, fetching, canonicalization, and snapshots

**Files:**
- Create: `src/academic_ingest/discovery/robots.py`
- Create: `src/academic_ingest/discovery/sitemap.py`
- Create: `src/academic_ingest/discovery/link_discovery.py`
- Create: `src/academic_ingest/discovery/source_map.py`
- Create: `src/academic_ingest/fetching/client.py`
- Create: `src/academic_ingest/fetching/rate_limit.py`
- Create: `src/academic_ingest/fetching/cache.py`
- Create: `src/academic_ingest/fetching/rendering.py`
- Create: `src/academic_ingest/snapshots/hashing.py`
- Create: `src/academic_ingest/snapshots/storage.py`
- Test: `tests/unit/test_source_scope.py`
- Test: `tests/unit/test_canonical_urls.py`
- Test: `tests/unit/test_robots.py`
- Test: `tests/unit/test_fetch_client.py`
- Test: `tests/unit/test_rate_limit.py`
- Test: `tests/unit/test_snapshot_hashing.py`

**Interfaces:**
- Produces: `AccessPolicy.evaluate(url: str) -> AccessDecision`.
- Produces: `canonicalize_url(url: str, html: bytes | None) -> str`.
- Produces: `SafeFetchClient.fetch(url: str, crawl_job_id: UUID) -> FetchResult`.
- Produces: `SnapshotStore.put(raw: bytes, suffix: str) -> StoredSnapshot`.

- [ ] **Step 1: Write failing SSRF, campus, retry, and hashing tests**

```python
def test_fetch_rejects_disallowed_host(fetch_client) -> None:
    with pytest.raises(UnsafeSourceError, match="allowlisted"):
        fetch_client.validate_url("https://example.com/policy")


def test_normalized_hash_ignores_insignificant_whitespace() -> None:
    assert normalized_hash(b"A  policy\nrow") == normalized_hash(b"A policy row")
```

- [ ] **Step 2: Run the acquisition test group and observe missing modules**

Run: `python -m pytest tests/unit/test_source_scope.py tests/unit/test_canonical_urls.py tests/unit/test_robots.py tests/unit/test_fetch_client.py tests/unit/test_rate_limit.py tests/unit/test_snapshot_hashing.py -q`
Expected: collection fails on missing acquisition modules.

- [ ] **Step 3: Implement the bounded acquisition boundary**

Require HTTPS, reject credentials and IP-literal hosts, resolve DNS before requests, reject private/reserved destinations, validate every redirect, cap response bytes, allow only configured content types, apply robots rules, rate-limit per host, cache validators, retry only transient failures, and return typed skipped decisions. Rendering remains an explicit unavailable/optional strategy rather than an automatic browser fallback.

- [ ] **Step 4: Run acquisition tests**

Run: `python -m pytest tests/unit/test_source_scope.py tests/unit/test_canonical_urls.py tests/unit/test_robots.py tests/unit/test_fetch_client.py tests/unit/test_rate_limit.py tests/unit/test_snapshot_hashing.py -q`
Expected: all tests pass with respx and no live network.

- [ ] **Step 5: Commit acquisition modules**

```text
git add src/academic_ingest/discovery src/academic_ingest/fetching src/academic_ingest/snapshots tests/unit
git commit -m "feat: add safe source acquisition and snapshots"
```

### Task 6: Adapter protocol, classification, glossary, and course catalog

**Files:**
- Create: `src/academic_ingest/adapters/base.py`
- Create: `src/academic_ingest/adapters/registry.py`
- Create: `src/academic_ingest/classification/page_classifier.py`
- Create: `src/academic_ingest/classification/rules.py`
- Create: `src/academic_ingest/adapters/uw/course_glossary.py`
- Create: `src/academic_ingest/adapters/uw/course_catalog.py`
- Create: `src/academic_ingest/adapters/uw/time_schedule.py`
- Create: `src/academic_ingest/adapters/uw/equivalency_guide.py`
- Create: `src/academic_ingest/adapters/generic_html.py`
- Create: `src/academic_ingest/adapters/pdf_policy.py`
- Create: `tests/fixtures/uw/html/course_glossary.html`
- Create: `tests/fixtures/uw/html/courses_cse.html`
- Create: `tests/fixtures/uw/html/courses_info.html`
- Create: `tests/fixtures/uw/html/courses_selected.html`
- Test: `tests/unit/test_adapter_registry.py`
- Test: `tests/unit/test_uw_course_catalog.py`
- Test: `tests/unit/test_conditional_adapters.py`
- Test: `tests/integration/test_course_ingestion.py`

**Interfaces:**
- Produces: `SourceAdapter.matches(page: ClassifiedPage) -> bool` and `extract(context: AdapterContext) -> AdapterResult`.
- Produces: `CourseCatalogAdapter.extract_course_blocks(html: bytes) -> list[CourseCandidate]`.
- Produces: parsed credits, general-education designators, evidence block selectors, prerequisites, restrictions, overlap, and offering language.
- Produces: conditional Time Schedule observations and Equivalency Guide discovery/snapshot candidates without unsupported policy mappings.
- Produces: bounded generic HTML and PDF evidence blocks for fixture ingestion and fallback extraction.

- [ ] **Step 1: Write failing tests for representative course blocks**

```python
def test_course_adapter_preserves_block_and_credit_range(course_context) -> None:
    result = CourseCatalogAdapter().extract(course_context)
    course = next(item for item in result.records if item.canonical_code == "CSE 4XX")
    assert (course.credits_min, course.credits_max) == (3, 5)
    assert course.evidence[0].css_selector == "#cse4xx"
    assert "Prerequisite:" in course.evidence[0].evidence_text
```

- [ ] **Step 2: Run course adapter tests and observe missing adapters**

Run: `python -m pytest tests/unit/test_adapter_registry.py tests/unit/test_uw_course_catalog.py tests/unit/test_conditional_adapters.py tests/integration/test_course_ingestion.py -q`
Expected: missing adapter modules.

- [ ] **Step 3: Implement deterministic page classification and course extraction**

Discover canonical subject links from the index, retain course DOM blocks, normalize subject codes containing spaces, parse fixed/ranged credits, separate general-education tokens, keep catalog offering prose historical, and route malformed blocks to review. Store the glossary as a versioned source rather than applying timeless constants.

- [ ] **Step 4: Run course adapter tests**

Run: `python -m pytest tests/unit/test_adapter_registry.py tests/unit/test_uw_course_catalog.py tests/unit/test_conditional_adapters.py tests/integration/test_course_ingestion.py -q`
Expected: all tests pass.

- [ ] **Step 5: Commit course adapters**

```text
git add src/academic_ingest/adapters src/academic_ingest/classification tests
git commit -m "feat: parse UW Seattle course catalog evidence"
```

### Task 7: Majors index and major-detail adapters

**Files:**
- Create: `src/academic_ingest/adapters/uw/majors_index.py`
- Create: `src/academic_ingest/adapters/uw/major_detail.py`
- Create: `tests/fixtures/uw/html/majors_index.html`
- Create: `tests/fixtures/uw/html/major_detail.html`
- Create: `tests/fixtures/uw/html/major_detail_conflict.html`
- Test: `tests/unit/test_uw_majors.py`
- Test: `tests/integration/test_major_ingestion.py`

**Interfaces:**
- Produces: `MajorsIndexAdapter` program summaries and official detail links.
- Produces: `MajorDetailAdapter` scoped requirements with mandatory and recommended preparation represented separately.

- [ ] **Step 1: Write failing major classification tests**

```python
def test_recommended_preparation_is_not_mandatory(major_detail_context) -> None:
    result = MajorDetailAdapter().extract(major_detail_context)
    preparation = next(item for item in result.requirements if item.name == "Competitive preparation")
    assert preparation.recommended is True
    assert preparation.mandatory is False
```

- [ ] **Step 2: Run major adapter tests and observe missing adapters**

Run: `python -m pytest tests/unit/test_uw_majors.py tests/integration/test_major_ingestion.py -q`
Expected: missing major adapter modules.

- [ ] **Step 3: Implement index/detail extraction with scope preservation**

Extract only official classifications, application requirements, timing, deadlines, GPA/grade floors, credit minima, source scope, departmental links, and required/recommended labels. Keep outcome statistics separate. Emit conflicting candidates rather than choosing between admissions, department, and catalog claims.

- [ ] **Step 4: Run major adapter tests**

Run: `python -m pytest tests/unit/test_uw_majors.py tests/integration/test_major_ingestion.py -q`
Expected: all tests pass.

- [ ] **Step 5: Commit major adapters**

```text
git add src/academic_ingest/adapters/uw tests
git commit -m "feat: parse UW major classifications and requirements"
```

### Task 8: Transfer admissions and transfer-credit adapters

**Files:**
- Create: `src/academic_ingest/adapters/uw/transfer_admissions.py`
- Create: `src/academic_ingest/adapters/uw/transfer_policies.py`
- Create: `tests/fixtures/uw/html/transfer_admissions.html`
- Create: `tests/fixtures/uw/html/transfer_policies.html`
- Test: `tests/unit/test_uw_transfer.py`
- Test: `tests/integration/test_transfer_ingestion.py`

**Interfaces:**
- Produces: separate `AdmissionsRule` and `TransferPolicy` candidates for each scoped table row or prose rule.
- Produces: table evidence containing heading, headers, row, notes, and footnotes.

- [ ] **Step 1: Write failing table-context and outcome tests**

```python
def test_transfer_table_retains_headers_and_footnote(transfer_context) -> None:
    result = TransferPolicyAdapter().extract(transfer_context)
    rule = next(item for item in result.records if item.policy_type == "lower_division_limit")
    assert rule.evidence[0].heading_context == "Transfer credit limits"
    assert "Credit source" in rule.evidence[0].evidence_text
    assert rule.evidence[0].footnote_context == "Limit applies toward the degree total."
```

- [ ] **Step 2: Run transfer tests and observe missing adapters**

Run: `python -m pytest tests/unit/test_uw_transfer.py tests/integration/test_transfer_ingestion.py -q`
Expected: missing transfer adapter modules.

- [ ] **Step 3: Implement scoped rules and table preservation**

Extract applicant definitions, term/deadline rows, notification periods, department distinctions, credit conversions, standing thresholds, lower-division and total limits, residence, degree applicability, duplicates, sequencing, explicit no-credit language, and DTA limitations. Never create no-credit from an absent mapping.

- [ ] **Step 4: Run transfer tests**

Run: `python -m pytest tests/unit/test_uw_transfer.py tests/integration/test_transfer_ingestion.py -q`
Expected: all tests pass.

- [ ] **Step 5: Commit transfer adapters**

```text
git add src/academic_ingest/adapters/uw tests
git commit -m "feat: parse UW transfer admissions and credit policies"
```

### Task 9: AP-credit adapter with score bands and notes

**Files:**
- Create: `src/academic_ingest/adapters/uw/ap_credit.py`
- Create: `tests/fixtures/uw/html/ap_credit.html`
- Test: `tests/unit/test_uw_ap_credit.py`
- Test: `tests/integration/test_ap_ingestion.py`

**Interfaces:**
- Produces: one `ExamCreditRule` per score band with aligned awarded courses and credits.
- Produces: subject, row, header, score-specific note, subject note, native-speaker restriction, duplicate-credit rule, placement effect, and unknown major applicability.

- [ ] **Step 1: Write failing multi-course and note tests**

```python
def test_ap_score_band_aligns_multiple_awards(ap_context) -> None:
    result = APCreditAdapter().extract(ap_context)
    rule = next(item for item in result.records if item.exam_name == "Calculus BC" and item.score_min == 5)
    assert rule.awarded_courses == ["MATH 124", "MATH 125"]
    assert rule.awarded_credit_values == [5, 5]
    assert rule.major_specific_applicability == "unknown"
```

- [ ] **Step 2: Run AP tests and observe the missing adapter**

Run: `python -m pytest tests/unit/test_uw_ap_credit.py tests/integration/test_ap_ingestion.py -q`
Expected: missing AP adapter module.

- [ ] **Step 3: Implement row-spanning AP table parsing**

Track inherited subject headings, explicit score bands, multiple course/credit awards, general-education designators, placement-only rows, zero/unknown credit, historical markers, row notes, nearby subject notes, duplicate credit, and native-speaker restrictions. Reject mismatched award/credit cardinality.

- [ ] **Step 4: Run AP tests**

Run: `python -m pytest tests/unit/test_uw_ap_credit.py tests/integration/test_ap_ingestion.py -q`
Expected: all tests pass.

- [ ] **Step 5: Commit AP adapter**

```text
git add src/academic_ingest/adapters/uw/ap_credit.py tests
git commit -m "feat: parse UW AP credit score bands"
```

### Task 10: Recursive prerequisite AST, parser, renderer, and evaluator

**Files:**
- Create: `src/academic_ingest/prerequisites/ast.py`
- Create: `src/academic_ingest/prerequisites/parser.py`
- Create: `src/academic_ingest/prerequisites/evaluator.py`
- Test: `tests/unit/test_prerequisite_ast.py`
- Test: `tests/unit/test_prerequisite_parser.py`
- Test: `tests/unit/test_prerequisite_evaluator.py`

**Interfaces:**
- Produces: discriminated recursive `RequirementNode` types with `to_json`, `from_json`, and `render`.
- Produces: `parse_requirement(text: str, evidence_id: UUID | None) -> RequirementNode`.
- Produces: `evaluate(node: RequirementNode, transcript: SyntheticTranscript) -> EvaluationResult`.

- [ ] **Step 1: Write failing nested-logic and unresolved tests**

```python
def test_parser_preserves_nested_and_or_logic() -> None:
    node = parse_requirement("MATH 124 and (CSE 121 or CSE 122), minimum grade 2.0")
    assert node.node_type == NodeType.ALL_OF
    assert node.children[1].node_type == NodeType.MINIMUM_GRADE
    assert node.children[1].children[0].node_type == NodeType.ANY_OF


def test_unknown_fragment_becomes_raw_unresolved() -> None:
    node = parse_requirement("CSE 123 and an approved advanced experience")
    assert any(child.node_type == NodeType.RAW_UNRESOLVED for child in node.walk())
```

- [ ] **Step 2: Run AST tests and observe missing modules**

Run: `python -m pytest tests/unit/test_prerequisite_ast.py tests/unit/test_prerequisite_parser.py tests/unit/test_prerequisite_evaluator.py -q`
Expected: missing prerequisite modules.

- [ ] **Step 3: Implement conservative recursive parsing and three-state evaluation**

Support every required node type. Parse explicit parentheses, conjunctions, disjunctions, concurrency, minimum grades, course codes, placement, permission, standing, scope restrictions, credit/GPA thresholds, and conditions. Return satisfied, unsatisfied, or unresolved; never treat unresolved as false.

- [ ] **Step 4: Run prerequisite tests**

Run: `python -m pytest tests/unit/test_prerequisite_ast.py tests/unit/test_prerequisite_parser.py tests/unit/test_prerequisite_evaluator.py -q`
Expected: all tests pass.

- [ ] **Step 5: Commit prerequisite engine**

```text
git add src/academic_ingest/prerequisites tests/unit
git commit -m "feat: preserve nested prerequisite expressions"
```

### Task 11: Validation, conflicts, confidence, review, and publishing

**Files:**
- Create: `src/academic_ingest/validation/evidence.py`
- Create: `src/academic_ingest/validation/logical.py`
- Create: `src/academic_ingest/validation/source_scope.py`
- Create: `src/academic_ingest/validation/dates.py`
- Create: `src/academic_ingest/validation/tables.py`
- Create: `src/academic_ingest/conflicts/models.py`
- Create: `src/academic_ingest/conflicts/detector.py`
- Create: `src/academic_ingest/confidence/rules.py`
- Create: `src/academic_ingest/confidence/scorer.py`
- Create: `src/academic_ingest/review/models.py`
- Create: `src/academic_ingest/review/service.py`
- Create: `src/academic_ingest/publishing/service.py`
- Create: `tests/fixtures/uw/expected/qa_cases.json`
- Test: `tests/unit/test_evidence_validation.py`
- Test: `tests/unit/test_logical_validation.py`
- Test: `tests/unit/test_conflicts.py`
- Test: `tests/unit/test_confidence.py`
- Test: `tests/integration/test_publishing_versions.py`

**Interfaces:**
- Produces: `validate_candidate(candidate, snapshot) -> ValidationReport`.
- Produces: `detect_conflicts(records: Sequence[PolicyRecord]) -> list[ConflictRecord]`.
- Produces: `score_confidence(factors: ConfidenceFactors) -> ConfidenceDecision`.
- Produces: `PublishingService.publish(batch, session) -> PublishResult`.

- [ ] **Step 1: Write failing evidence, conflict, and publish-gate tests**

```python
def test_evidence_quote_must_exist_in_snapshot() -> None:
    report = validate_evidence("Minimum grade 2.5", b"Minimum grade 2.0")
    assert report.accepted is False
    assert report.code == "evidence_not_found"


async def test_policy_without_evidence_is_not_published(publisher, candidate) -> None:
    candidate.evidence = []
    result = await publisher.publish([candidate])
    assert result.published == []
    assert result.review_tasks[0].reason == "missing_exact_evidence"
```

- [ ] **Step 2: Run governance tests and observe missing modules**

Run: `python -m pytest tests/unit/test_evidence_validation.py tests/unit/test_logical_validation.py tests/unit/test_conflicts.py tests/unit/test_confidence.py tests/integration/test_publishing_versions.py -q`
Expected: missing governance modules.

- [ ] **Step 3: Implement deterministic governance**

Implement every validation rule from the request with explicit severity and disposition. Compare overlapping claims field-by-field. Store factor-level confidence explanations. Create review tasks for ambiguity and material change. Append record versions and current pointers transactionally while retaining evidence and prior versions.

Represent every required QA scenario in `qa_cases.json`, including direct equivalency without major applicability, many-to-one mappings, multi-course exam awards, unknown major applicability, higher major grade floors, nested logic, source conflict, critical footnote, unclear catalog year, explicit no credit, no mapping result, and recommended preparation.

- [ ] **Step 4: Run governance tests**

Run: `python -m pytest tests/unit/test_evidence_validation.py tests/unit/test_logical_validation.py tests/unit/test_conflicts.py tests/unit/test_confidence.py tests/integration/test_publishing_versions.py -q`
Expected: all tests pass.

- [ ] **Step 5: Commit governance and publication**

```text
git add src/academic_ingest/validation src/academic_ingest/conflicts src/academic_ingest/confidence src/academic_ingest/review src/academic_ingest/publishing tests
git commit -m "feat: gate policy publication on evidence and confidence"
```

### Task 12: Structured extraction clients and page-isolated pipeline jobs

**Files:**
- Create: `src/academic_ingest/extraction/client.py`
- Create: `src/academic_ingest/extraction/fake_client.py`
- Create: `src/academic_ingest/extraction/openai_client.py`
- Create: `src/academic_ingest/extraction/prompts.py`
- Create: `src/academic_ingest/extraction/schemas/policy.py`
- Create: `src/academic_ingest/jobs/ingest_job.py`
- Create: `src/academic_ingest/jobs/crawl_job.py`
- Test: `tests/unit/test_fake_extraction.py`
- Test: `tests/unit/test_openai_evidence_gate.py`
- Test: `tests/integration/test_pipeline.py`

**Interfaces:**
- Produces: async `StructuredExtractionClient` protocol methods named in the request.
- Produces: `run_ingest_job(inputs, extraction_client, repositories) -> PipelineResult`.
- Produces: prompt version, schema version, model ID, request ID, usage, validation, and retry metadata without secrets.

- [ ] **Step 1: Write failing fake-client and page-isolation tests**

```python
async def test_pipeline_continues_after_one_page_fails(pipeline, good_page, bad_page) -> None:
    result = await pipeline.run([bad_page, good_page])
    assert len(result.errors) == 1
    assert len(result.records) == 1
    assert result.parser_metrics.pages_attempted == 2
```

- [ ] **Step 2: Run extraction/pipeline tests and observe missing modules**

Run: `python -m pytest tests/unit/test_fake_extraction.py tests/unit/test_openai_evidence_gate.py tests/integration/test_pipeline.py -q`
Expected: missing extraction and job modules.

- [ ] **Step 3: Implement strict clients and stage orchestration**

Use the official OpenAI SDK structured-output API behind dependency injection. Send bounded cleaned text, tables, DOM blocks, deterministic fields, source context, and no credentials or arbitrary pages. Validate exact quotes before accepting output. Execute discovery through publishing as separate typed functions and collect all warnings, errors, skipped inputs, review tasks, links, snapshots, and metrics.

- [ ] **Step 4: Run extraction and pipeline tests**

Run: `python -m pytest tests/unit/test_fake_extraction.py tests/unit/test_openai_evidence_gate.py tests/integration/test_pipeline.py -q`
Expected: all tests pass with no OpenAI credential.

- [ ] **Step 5: Commit extraction and jobs**

```text
git add src/academic_ingest/extraction src/academic_ingest/jobs tests
git commit -m "feat: orchestrate evidence-verified ingestion jobs"
```

### Task 13: FastAPI endpoints and review resolution

**Files:**
- Create: `src/academic_ingest/api/app.py`
- Create: `src/academic_ingest/api/dependencies.py`
- Create: `src/academic_ingest/api/schemas/common.py`
- Create: `src/academic_ingest/api/routes/crawl_jobs.py`
- Create: `src/academic_ingest/api/routes/pages.py`
- Create: `src/academic_ingest/api/routes/sources.py`
- Create: `src/academic_ingest/api/routes/courses.py`
- Create: `src/academic_ingest/api/routes/programs.py`
- Create: `src/academic_ingest/api/routes/policies.py`
- Create: `src/academic_ingest/api/routes/conflicts.py`
- Create: `src/academic_ingest/api/routes/review_tasks.py`
- Test: `tests/integration/test_api.py`

**Interfaces:**
- Produces: `create_app(settings: Settings | None = None) -> FastAPI`.
- Produces: every endpoint and filter in request section 23.
- Produces: review resolution that appends reviewer decision metadata and leaves original evidence unchanged.

- [ ] **Step 1: Write failing health, fixture-ingest, retrieval, and review tests**

```python
def test_health_reports_database(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["database"] == "ok"


def test_course_detail_includes_evidence_and_versions(client, seeded_course) -> None:
    payload = client.get(f"/courses/{seeded_course.id}").json()
    assert payload["evidence"]
    assert len(payload["versions"]) >= 1
```

- [ ] **Step 2: Run API tests and observe missing application**

Run: `python -m pytest tests/integration/test_api.py -q`
Expected: missing API application.

- [ ] **Step 3: Implement thin route handlers over repositories and jobs**

Validate local fixture uploads without network, bound crawl-job inputs to configured UW seeds, return status/count/warning/error summaries, support all filters, include evidence/conflict/version relationships, and record review resolutions transactionally.

- [ ] **Step 4: Run API tests**

Run: `python -m pytest tests/integration/test_api.py -q`
Expected: all tests pass.

- [ ] **Step 5: Commit API**

```text
git add src/academic_ingest/api tests/integration/test_api.py
git commit -m "feat: expose academic ingestion API"
```

### Task 14: Sample ingestion, export, documentation, and full verification

**Files:**
- Create: `scripts/inspect_uw_sources.py`
- Create: `scripts/ingest_uw_sample.py`
- Create: `scripts/export_uw_records.py`
- Create: `src/academic_ingest/observability.py`
- Create: `docs/uw-adapter.md`
- Create: `docs/data-model.md`
- Create: `docs/pipeline.md`
- Create: `docs/adding-an-institution.md`
- Create: `docs/safety-and-compliance.md`
- Create: `AGENTS.md`
- Modify: `README.md`
- Test: `tests/integration/test_fixture_sample.py`
- Test: `tests/integration/test_export.py`
- Test: `tests/integration/test_all_published_records_have_evidence.py`
- Test: `tests/unit/test_source_inspection_output.py`

**Interfaces:**
- Produces: `ingest_uw_sample.py --fixture-only` and guarded `--allow-network` mode.
- Produces: `inspect_sources(urls: Sequence[str], allow_network: bool) -> list[InspectionResult]` using the Task 5 access boundary.
- Produces: `export_uw_records.py --output PATH` with schema version and UTC export timestamp.
- Produces: structured logs and counters with no raw page bodies.

- [ ] **Step 1: Write failing fixture summary, export, and evidence-invariant tests**

```python
def test_fixture_sample_publishes_only_evidenced_records(sample_database) -> None:
    summary = run_fixture_sample(sample_database)
    assert summary.records_published > 0
    assert summary.records_without_evidence == 0


def test_export_excludes_raw_snapshot_bytes(export_payload) -> None:
    assert export_payload["schema_version"] == "1.0"
    assert "raw_content" not in json.dumps(export_payload)


def test_inspection_requires_explicit_network_permission() -> None:
    results = inspect_sources(["https://www.washington.edu/students/crscat/"], allow_network=False)
    assert results[0].warnings == ["network_disabled"]
```

- [ ] **Step 2: Run end-to-end tests and observe missing scripts/docs integration**

Run: `python -m pytest tests/unit/test_source_inspection_output.py tests/integration/test_fixture_sample.py tests/integration/test_export.py tests/integration/test_all_published_records_have_evidence.py -q`
Expected: missing script and observability modules.

- [ ] **Step 3: Implement scripts, observability, and operator documentation**

Fixture ingestion loads only saved synthetic pages, prints a crawl summary, and stores records/evidence/version data. Export excludes secrets and raw binary snapshots. README documents setup, environment, Docker, migrations, fixture/live modes, tests, and limitations. The requested docs describe exact adapters, schema, Mermaid pipeline, institution extension, robots/access controls, retention, untrusted input, and review.

- [ ] **Step 4: Run the complete offline quality gate**

Run: `python -m ruff check .`
Expected: exit 0.

Run: `python -m ruff format --check .`
Expected: exit 0.

Run: `python -m mypy src`
Expected: exit 0 with no issues.

Run: `python -m pytest`
Expected: all tests pass without live network or OpenAI credentials.

Run: `npm run typecheck && npm run lint && npm run build`
Expected: all existing frontend checks pass.

- [ ] **Step 5: Verify PostgreSQL migration and fixture commands**

Run: `docker compose up -d postgres`
Expected: PostgreSQL reports healthy.

Run: `python -m alembic upgrade head`
Expected: migration `20260716_0001` applies successfully.

Run: `python scripts/ingest_uw_sample.py --fixture-only`
Expected: zero fatal errors and zero published records without evidence.

Run: `python scripts/export_uw_records.py --output tmp/uw-records.json`
Expected: valid JSON with schema version, export timestamp, normalized records, and evidence.

- [ ] **Step 6: Review fixture output and optionally run bounded live inspection**

Manually inspect exported prerequisites, admissions rules, transfer policies, AP score bands, unresolved items, conflicts, and review tasks. If a crawler contact email is configured, run `python scripts/inspect_uw_sources.py --allow-network`; report each inaccessible, denied, or changed source without converting it to success.

- [ ] **Step 7: Commit complete operator surface**

```text
git add README.md AGENTS.md docs scripts src/academic_ingest/observability.py tests
git commit -m "docs: complete UW ingestion operations and validation"
```

## Plan Self-Review Mapping

- Repository inspection and product specifications: completed before this plan; canonical paths handled in Task 1.
- Source discovery, robots, sitemaps, canonical metadata, and bounded inspection: Tasks 2 and 5.
- Core Pydantic/SQLAlchemy models, migration, evidence, and versions: Tasks 3 and 4.
- Safe fetching, snapshots, caching, retries, SSRF protection, and campus scope: Task 5.
- UW glossary, course, major, transfer, and AP adapters: Tasks 6 through 9.
- Time Schedule and Equivalency Guide: classified and documented in Tasks 2 and 6; enabled only under the specification's access/stability conditions.
- Recursive prerequisites and unresolved fragments: Task 10.
- GPT fallback, exact evidence verification, fake client, and offline behavior: Tasks 11 and 12.
- Validation, conflicts, confidence, review routing, versioned publishing, and material changes: Tasks 4 and 11.
- API endpoints: Task 13.
- Scripts, observability, documentation, full offline suite, PostgreSQL migration, fixture ingestion, and export: Task 14.
- Every requested QA semantic distinction is assigned to adapter, AST, validation, or publishing tests in Tasks 3 and 6 through 14.
