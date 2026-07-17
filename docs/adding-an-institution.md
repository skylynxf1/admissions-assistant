# Adding an institution

The core pipeline is institution independent. Institution-specific knowledge belongs in configuration,
classification rules, adapters, fixtures, and source documentation.

## 1. Define the boundary

Add `config/institutions/<institution>.yaml` with a stable institution/campus ID, official domains,
disallowed campus patterns, seed URLs, enabled policy families, and conservative request limits.
Seeds must be HTTPS URLs accepted by the same configuration. Keep campuses separate when their
catalogs or policies differ.

## 2. Inspect before parsing

Use the safe inspection boundary with network disabled first, then explicitly enable live inspection
with an operator contact email. Record robots decisions, sitemap/canonical behavior, content types,
authentication boundaries, update cadence, and whether a stable public API/file exists. Never treat
an inaccessible source as successfully inspected.

Create `docs/<institution>-source-map.md` with the inspection date and decision for every source.

## 3. Add classification and adapters

Add narrow path rules and adapters under `src/academic_ingest/adapters/<institution>/`. Reuse generic
domain models, evidence, prerequisites, validation, conflicts, confidence, review, and publishing.
Do not fork these core stages for the institution.

Implement deterministic selectors for stable structures. Preserve whole table context and exact
quotes. Emit unresolved warnings for ambiguous prose. Use the structured extraction protocol only
when deterministic parsing cannot safely represent the source.

## 4. Build synthetic fixtures and tests

Create small synthetic fixtures covering normal and adversarial structures. Test classification,
adapter selection, evidence quote verification, table footnotes, effective periods, nested logic,
unknown values, explicit no-credit wording, conflicts, and page-isolated failures. Tests must run
without network or model credentials.

## 5. Register and document

Register adapters in the application registry, add fixture ingestion coverage, document limitations,
and update export/API expectations. Run Python, frontend, and migration quality gates. A live rollout
should begin in snapshot/review mode; enable unattended publication only after evidence and change
behavior have been reviewed.
