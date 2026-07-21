# Transfer Equivalency Sources

Data backing `/transfer/outcomes` for the `bellevue-college -> uw-seattle` pathway
is produced by a **deterministic parser**, not hand-transcription. This
supersedes the earlier hand-curated dataset (a 15-record subset, once
transcribed by hand from the same guide and briefly the endpoint's source of
record); the hand-curated module (`academic_ingest.transfer.curated_equivalencies`)
has been deleted.

## What the parser does

`academic_ingest.adapters.uw.bellevue_equivalency.parse_bellevue_equivalencies`
walks every row of the UW Office of Admissions' official public Bellevue
College Equivalency Guide,
`https://admit.washington.edu/apply/transfer/equivalency-guide/bellevue/`,
and turns each row into an `EquivalencyRecord` — or, when a row's destination
text is conditional, ambiguous, or names more than one concrete destination,
into a `ReviewRow` held out of the published records for human review instead
of being guessed at. It never invents a mapping: every `EquivalencyRecord`
carries an `evidence_refs` entry that quotes the exact source/destination cell
text the record was built from.

Row handling:
- `<tr class="obsRow">` rows (superseded/historical entries) are skipped.
- A row whose destination cell is empty, or whose source cell says "see ...
  combined entry" (a cross-reference into another row), is skipped.
- A destination naming more than one course, or written with conditional
  language ("if", "otherwise", ";"), goes to `review_rows`, not `records`.
- Everything else becomes a `direct_equivalent`, `sequence_equivalent` (2+
  source courses map to sequence credit), `general_elective` (wildcard "1XX"/
  "2XX" destination), or `no_credit` record.

## Guide snapshot and provenance

- **Retrieved:** 2026-07-21, from
  `https://admit.washington.edu/apply/transfer/equivalency-guide/bellevue/`.
- **Snapshot location:** the fetched HTML is bundled as package data at
  `src/academic_ingest/data/equivalency_guide_bellevue.html` and loaded via
  `importlib.resources` (see `academic_ingest.transfer.guide_source`), so
  parsing needs no network access and no database. A copy also lives at
  `tests/fixtures/uw/html/equivalency_guide_bellevue_2026.html` for the parser's
  own offline tests (`tests/adapters/test_bellevue_equivalency.py`).
- **Parsed once per process:** `guide_source.load_bellevue_guide_records()`
  caches the parse result at module level; both the `/transfer/outcomes`
  endpoint (`academic_ingest.api.routes.transfer.get_equivalency_repository`)
  and the Supabase publisher CLI (`academic_ingest.publishing.equivalency_publisher`)
  read from this single cached source, so serving and publishing never
  disagree.

## Coverage summary (this snapshot)

| Pathway | Records | Held for review | Notes |
| --- | --- | --- | --- |
| Bellevue College → UW Seattle | **633** published `EquivalencyRecord`s (130 `direct_equivalent`, 502 `general_elective`, 1 `no_credit`; `sequence_equivalent` when applicable). | 51 `ReviewRow`s (45 ambiguous destinations, 6 conditional) — not published, pending human review. | 834 obsolete rows and 4 cross-reference rows are intentionally skipped, not published. |
| Seattle University → UW Seattle | **0.** No published course-by-course equivalency guide exists. | — | See "Seattle University" below; unchanged from the prior hand-curated dataset. |

Review rows and skip counts are recomputed from the source HTML by the parser
itself (`ParseResult.review_rows` / `ParseResult.skipped`) — this table is a
snapshot, not a separately maintained source of truth. Run the parser tests
(`tests/adapters/test_bellevue_equivalency.py`) or
`tests/transfer/test_guide_source.py` to see current counts.

## Seattle University → UW Seattle

**No records**, same conclusion as before, reached the same way: this pathway
is not produced by a parser because no course-by-course source page exists to
parse.

- UW Office of Admissions' equivalency-guide index,
  `https://admit.washington.edu/apply/transfer/equivalency-guide/` (retrieved
  2026-07-20): lists only Washington's public community and technical colleges
  (34 institutions, including Bellevue College and the public "Seattle
  Colleges" district — North/Central/South Seattle College, which is a
  **different institution** from the private Seattle University). Seattle
  University does not appear in this index.
- Seattle University Office of the Registrar, "Transfer Tools",
  `https://www.seattleu.edu/office-of-the-registrar/transfer-tools/` (retrieved
  2026-07-20): covers only credit Seattle University accepts **incoming** from
  other schools; it does not publish outgoing equivalencies to UW or mention UW
  at all.
- General web search for a Seattle University ↔ UW articulation agreement or
  course-by-course transfer credit PDF returned no such document; UW's transfer
  credit policy for four-year institutions
  (`https://admit.washington.edu/apply/transfer/policies/`, referenced but not
  itself a course-level source) confirms that transfer from four-year schools
  like Seattle University is evaluated individually by UW's admissions office
  rather than through a pre-published table.

This matches the expected pattern: Seattle University is a private four-year
institution and, unlike Washington's public community colleges, has no
published course-equivalency guide with UW. No mappings are fabricated or
guessed to fill this gap — the resolver reports `not_found` for every Seattle
University course, which is the honest outcome given the absence of a
published source.
