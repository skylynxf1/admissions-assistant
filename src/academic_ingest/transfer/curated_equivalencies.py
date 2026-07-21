"""Curated, CITED published transfer-equivalency records.

Every `EquivalencyRecord` below was transcribed by hand from a public page that was
actually fetched during research for this module (retrieved 2026-07-20). Nothing
here is inferred, guessed, or generated — if a course is not listed, that simply
means no published equivalency was found for it (the resolver reports
`not_found` for such courses; this module never asserts a `no_credit` outcome that
the source did not explicitly state).

Sources
-------
Bellevue College -> UW Seattle: the UW Office of Admissions' official public
Bellevue College Equivalency Guide,
https://admit.washington.edu/apply/transfer/equivalency-guide/bellevue/
(retrieved 2026-07-20), cross-referenced against
https://admit.washington.edu/equivalency-guide-manual (retrieved 2026-07-20) for
the notation legend (specific UW course number = direct equivalent; department
prefix + "1XX"/"2XX" = departmental elective credit; generic "UW 1XX"/"2XX" =
general elective credit; "No credit" = explicit no-credit).

Seattle University -> UW Seattle: NO published course-by-course equivalency guide
was found. The UW Office of Admissions' equivalency-guide system
(https://admit.washington.edu/apply/transfer/equivalency-guide/, retrieved
2026-07-20) is explicitly scoped to Washington's public community and technical
colleges; Seattle University does not appear in that list. Seattle University's
own Registrar "Transfer Tools" page
(https://www.seattleu.edu/office-of-the-registrar/transfer-tools/, retrieved
2026-07-20) covers only incoming transfer credit (courses transferring IN to
Seattle University), not outgoing equivalencies to UW. No Seattle University
records are included here as a result — see docs/equivalencies/SOURCES.md for
the full account of what was searched and why nothing qualified.
"""

from __future__ import annotations

from academic_ingest.transfer.models import EquivalencyRecord

_BELLEVUE_GUIDE_URL = "https://admit.washington.edu/apply/transfer/equivalency-guide/bellevue/"
_BELLEVUE_EVIDENCE = [
    f"{_BELLEVUE_GUIDE_URL} (retrieved 2026-07-20)",
    "UW Office of Admissions — Bellevue College Equivalency Guide (official)",
]


def _bellevue_record(
    *,
    source_course_codes: list[str],
    mapping_type: str,
    destination_outcome: str,
    credits_awarded: float | None = None,
    notation: str | None = None,
) -> EquivalencyRecord:
    """Build an EquivalencyRecord sourced from the Bellevue College guide.

    `notation` records the guide's own area-of-inquiry / requirement tag (e.g.
    "NSc [RSN]", "[C]", "A&H") verbatim, when the guide showed one, for
    traceability — it is not interpreted or relied upon by the resolver.
    """
    conditions: dict[str, object] = {"guide_notation": notation} if notation else {}
    return EquivalencyRecord(
        source_course_codes=source_course_codes,
        mapping_type=mapping_type,
        destination_outcome=destination_outcome,
        credits_awarded=credits_awarded,
        conditions=conditions,
        evidence_refs=list(_BELLEVUE_EVIDENCE),
    )


def curated_records() -> dict[tuple[str, str], list[EquivalencyRecord]]:
    """Verified, cited equivalency records keyed by (source, destination) slugs.

    Only `("bellevue-college", "uw-seattle")` is populated. No public,
    course-by-course Seattle University -> UW Seattle equivalency source was
    found during research (see module docstring and
    docs/equivalencies/SOURCES.md), so `("seattle-university", "uw-seattle")`
    intentionally has no entry here — the resolver will report `not_found` for
    every Seattle University course, which is the honest outcome given the
    absence of a published source, not a fabricated `no_credit`.
    """
    bellevue_records = [
        # --- Direct equivalents ---
        _bellevue_record(
            source_course_codes=["CS 101"],
            mapping_type="direct_equivalent",
            destination_outcome="UW CSE 100",
            credits_awarded=5.0,
            notation="NSc [RSN]",
        ),
        _bellevue_record(
            source_course_codes=["CS 211"],
            mapping_type="direct_equivalent",
            destination_outcome="UW CSE 143",
            credits_awarded=5.0,
            notation="NSc [RSN]",
        ),
        _bellevue_record(
            source_course_codes=["MATH& 142"],
            mapping_type="direct_equivalent",
            destination_outcome="UW MATH 120",
            credits_awarded=5.0,
            notation="NSc [RSN]",
        ),
        _bellevue_record(
            source_course_codes=["MATH& 151"],
            mapping_type="direct_equivalent",
            destination_outcome="UW MATH 124",
            credits_awarded=5.0,
            notation="NSc [RSN]",
        ),
        _bellevue_record(
            source_course_codes=["MATH& 152"],
            mapping_type="direct_equivalent",
            destination_outcome="UW MATH 125",
            credits_awarded=5.0,
            notation="NSc",
        ),
        _bellevue_record(
            source_course_codes=["ECON& 201"],
            mapping_type="direct_equivalent",
            destination_outcome="UW ECON 200",
            credits_awarded=5.0,
            notation="SSc [RSN]",
        ),
        _bellevue_record(
            source_course_codes=["ECON& 202"],
            mapping_type="direct_equivalent",
            destination_outcome="UW ECON 201",
            credits_awarded=5.0,
            notation="SSc [RSN]",
        ),
        _bellevue_record(
            source_course_codes=["ENGL& 101"],
            mapping_type="direct_equivalent",
            destination_outcome="UW ENGL 131",
            credits_awarded=5.0,
            notation="[C]",
        ),
        _bellevue_record(
            source_course_codes=["PSYC& 100"],
            mapping_type="direct_equivalent",
            destination_outcome="UW PSYCH 101",
            credits_awarded=5.0,
            notation="SSc",
        ),
        _bellevue_record(
            source_course_codes=["ANTH& 100"],
            mapping_type="direct_equivalent",
            destination_outcome="UW ANTH 100",
            credits_awarded=5.0,
            notation="SSc",
        ),
        _bellevue_record(
            source_course_codes=["ANTH& 204"],
            mapping_type="direct_equivalent",
            destination_outcome="UW ARCHY 205",
            credits_awarded=5.0,
            notation="SSc",
        ),
        _bellevue_record(
            source_course_codes=["ART 201"],
            mapping_type="direct_equivalent",
            destination_outcome="UW ART H 201",
            credits_awarded=5.0,
            notation="A&H",
        ),
        # --- Departmental elective credit (department prefix retained, e.g.
        # "ART 1XX": transfers, corresponds to the department, but not to one
        # specific UW course number) ---
        _bellevue_record(
            source_course_codes=["ART 101"],
            mapping_type="departmental_elective",
            destination_outcome="UW ART 1XX (elective credit, no specific course match)",
            credits_awarded=5.0,
            notation="A&H",
        ),
        # --- General elective credit (generic "UW 1XX": transfers but does not
        # correspond to any specific UW department or program) ---
        _bellevue_record(
            source_course_codes=["NURS 100X"],
            mapping_type="general_elective",
            destination_outcome="UW 1XX (general elective credit; limited-credit nursing course)",
            credits_awarded=7.0,
            notation="[LC]",
        ),
        # --- Explicit no credit ---
        _bellevue_record(
            source_course_codes=["BUS 145"],
            mapping_type="no_credit",
            destination_outcome="No credit",
        ),
    ]
    return {
        ("bellevue-college", "uw-seattle"): bellevue_records,
    }
