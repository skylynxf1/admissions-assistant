# Curated Transfer Equivalency Sources

Data backing `src/academic_ingest/transfer/curated_equivalencies.py`, transcribed
by hand from public web pages actually fetched during research on 2026-07-20.
This is a **manually curated, cited dataset**, not an automated ingest — it is a
stand-in for the real pipeline until automated snapshot ingestion (fetch +
diff + evidence storage) lands for these institutions.

## Coverage summary

| Pathway | Verified data? |
| --- | --- |
| Bellevue College → UW Seattle | **Yes.** 15 records, all sourced from the UW Office of Admissions' official public Bellevue College Equivalency Guide. |
| Seattle University → UW Seattle | **No.** No published course-by-course equivalency guide exists. See "Seattle University — what was searched and why nothing qualifies" below. Zero records are included for this pathway; the resolver will correctly report `not_found` for every Seattle University course rather than a fabricated outcome. |

Absence of a Seattle University mapping is intentional and required by the task's
integrity rules — it is never represented as `no_credit`/`explicit_no_credit`.

## Bellevue College → UW Seattle

Primary source (official, UW Office of Admissions):
`https://admit.washington.edu/apply/transfer/equivalency-guide/bellevue/`
(retrieved 2026-07-20).

Notation legend cross-referenced from the UW Office of Admissions'
`https://admit.washington.edu/equivalency-guide-manual` (retrieved 2026-07-20):
a specific UW course number = direct equivalent; a department prefix followed by
`1XX`/`2XX` (e.g. `ART 1XX`) = departmental elective credit (corresponds to a
UW department/program but not one specific course); a generic `UW 1XX`/`2XX`
prefix = general elective credit (does not correspond to any specific UW
department); "No credit" = explicit no-credit.

| Source course(s) (as published) | UW destination outcome (as published) | Credits | `mapping_type` | Source type | Retrieved | Confidence |
| --- | --- | --- | --- | --- | --- | --- |
| CS 101 | CSE 100 | 5 | `direct_equivalent` | official | 2026-07-20 | high |
| CS 211 | CSE 143 | 5 | `direct_equivalent` | official | 2026-07-20 | high |
| MATH& 142 | MATH 120 | 5 | `direct_equivalent` | official | 2026-07-20 | high |
| MATH& 151 | MATH 124 | 5 | `direct_equivalent` | official | 2026-07-20 | high |
| MATH& 152 | MATH 125 | 5 | `direct_equivalent` | official | 2026-07-20 | high |
| ECON& 201 | ECON 200 | 5 | `direct_equivalent` | official | 2026-07-20 | high |
| ECON& 202 | ECON 201 | 5 | `direct_equivalent` | official | 2026-07-20 | high |
| ENGL& 101 | ENGL 131 | 5 | `direct_equivalent` | official | 2026-07-20 | high |
| PSYC& 100 | PSYCH 101 | 5 | `direct_equivalent` | official | 2026-07-20 | high |
| ANTH& 100 | ANTH 100 | 5 | `direct_equivalent` | official | 2026-07-20 | high |
| ANTH& 204 | ARCHY 205 | 5 | `direct_equivalent` | official | 2026-07-20 | high |
| ART 201 | ART H 201 | 5 | `direct_equivalent` | official | 2026-07-20 | high |
| ART 101 | ART 1XX (elective credit, no specific course match) | 5 | `departmental_elective` | official | 2026-07-20 | high |
| NURS 100X | UW 1XX (general elective credit; limited-credit nursing course) | 7 | `general_elective` | official | 2026-07-20 | high |
| BUS 145 (formerly G BUS 145) | No credit | — | `no_credit` | official | 2026-07-20 | high |

All 15 rows above cite the same URL:
`https://admit.washington.edu/apply/transfer/equivalency-guide/bellevue/`
(retrieved 2026-07-20). Each was independently transcribed from at least one
fetch of that page targeted at its specific subject area (Computer Science,
Mathematics, Economics, English, Psychology, Anthropology, Art, Nursing,
Business), and the CS/Math/Econ/English rows and the Chemistry/Biology/Nursing
rows were each cross-checked across two separate fetches of the same page for
consistency. Confidence is "high" because the source is UW's own official
admissions equivalency guide, the canonical public source UW itself directs
transfer applicants to.

Data that was found on the same page but deliberately **excluded** from the
curated set because it did not cleanly fit a single `EquivalencyRecord` (to
avoid misrepresenting a composite/split outcome as something simpler than it
is) — noted here for transparency, not fabricated as a mapping:
- `CS 210 (5)` → `CSE 142 (4), CSE 2XX (1)` — a split outcome (4 direct credits +
  1 elective credit) that the current single-outcome `EquivalencyRecord` shape
  does not cleanly represent without misstating either the direct or the
  elective portion.
- `BIOL& 211, 212, 213` → `BIOL 180, 200, 220 (5,5,5), 2XX (3)` — each Bellevue
  course maps individually to its corresponding UW course (not a genuine
  "must-take-all-together" sequence), so it does not fit `sequence_equivalent`
  either; representing it correctly would require 1:1 records per course pair,
  which was left for a follow-up pass rather than guessed at here.
- `CHEM&` and further `BIOL&`/`NURS` rows beyond those listed above were seen
  during research (e.g. `CHEM& 121`, `CHEM& 131`, `CHEM& 161`, `CHEM& 162`,
  `CHEM& 263`, `BIOL& 100`, `BIOL& 241/242`) but were not included in this pass
  purely to keep the curated set to a reviewable size — they are real,
  verified, and available on the same cited page for a follow-up expansion.

## Seattle University → UW Seattle

**No records.** What was searched and found:

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

This matches the expected pattern described in the task brief: Seattle
University is a private four-year institution and, unlike Washington's public
community colleges, has no published course-equivalency guide with UW. Per the
integrity rules for this task, no mappings were fabricated or guessed to fill
this gap.
