# UW Seattle adapter guide

## Scope and source families

The UW adapter targets only the Seattle campus and the exact HTTPS hosts in
`config/institutions/uw_seattle.yaml`. The inspected source inventory, robots decisions, canonical
metadata, and access limitations are recorded in [uw-source-map.md](uw-source-map.md).

| Adapter | Source family | Output | Important boundary |
|---|---|---|---|
| `uw.course_catalog` | Course catalog department pages | `Course` | Variable credits, overlap/equivalence, prerequisites, and offering notes remain separate fields. |
| `uw.course_glossary` | Catalog glossary | Evidence blocks/definitions | Definitions inform normalization; they do not invent course policy. |
| `uw.majors_index` | Admissions majors index | `Program` | Open, minimum-requirements, and capacity-constrained classifications are source scoped. |
| `uw.major_detail` | Department/major page | `Program`, `Requirement` | Mandatory requirements and recommended preparation remain distinct. |
| `uw.transfer_admissions` | Transfer application pages | `AdmissionsRule` | Applicant type, deadlines, notification timing, and departmental distinctions are separate claims. |
| `uw.transfer_policies` | Transfer policy page | `TransferPolicy` | Table headers, rows, heading context, notes, and footnotes stay attached to evidence. |
| `uw.ap_credit` | AP credit table | `ExamCreditRule` | One score band per rule; multi-course awards retain course/credit cardinality and nearby notes. |
| `uw.time_schedule` | Public Time Schedule index | Links/observations | NetID-protected section details are never followed. Observed offerings are not future guarantees. |
| `uw.equivalency_guide` | Transfer Equivalency Guide | Discovery links | Snapshot/discovery only until a stable public interface is confirmed. |

## Evidence behavior

Each adapter builds `EvidenceRecord` objects with the source snapshot ID, canonical URL, page title,
exact visible text, heading/table/row/footnote context when relevant, parser name/version, retrieval
time, authority, and review status. The publication gate normalizes whitespace conservatively and
rejects any quote that is absent from the named snapshot.

For tables, evidence includes enough context to prevent a detached cell from changing meaning. A
critical footnote is stored alongside the row instead of being summarized away.

## Semantic decisions

- A direct equivalency does not imply major applicability.
- A missing mapping is `not_found`, never `explicit_no_credit`.
- Explicit no-credit outcomes require affirmative source language.
- Course enrollment prerequisites, major-admission prerequisites, degree requirements, residency,
  and recommended preparation use different requirement scopes.
- A higher major-specific grade floor does not overwrite a lower catalog enrollment prerequisite.
- UW “Data Science” source text is represented in its stated curricular/program context; the adapter
  does not manufacture a standalone major.
- Unclear catalog years and effective dates stay null and route to review where material.

## Updating an adapter

Save a minimal synthetic fixture that represents the source structure without copying unnecessary
page content. Write a failing unit test for the semantic edge case and an integration test through
classification/registry. Increment the adapter version, preserve prior snapshots, and run the full
quality gate. If the public source surface changed, update `uw-source-map.md` with the inspection date
and access decision.
