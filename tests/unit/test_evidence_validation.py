from uuid import uuid4

from academic_ingest.models.domain import Course, EvidenceRecord
from academic_ingest.models.enums import AuthorityTier, ConfidenceTier
from academic_ingest.validation.evidence import validate_candidate, validate_evidence


def _evidence(text: str, *, snapshot_id=None) -> EvidenceRecord:
    return EvidenceRecord(
        source_snapshot_id=snapshot_id or uuid4(),
        source_url="https://www.washington.edu/students/crscat/cse.html",
        page_title="Computer Science and Engineering",
        evidence_text=text,
        parser_name="course_catalog",
        parser_version="1.0",
        authority_tier=AuthorityTier.OFFICIAL_CATALOG,
        confidence_tier=ConfidenceTier.HIGH_CONFIDENCE,
    )


def _course(evidence: list[EvidenceRecord]) -> Course:
    return Course(
        institution_id="uw-seattle",
        subject="CSE",
        number="123",
        title="Introduction to Computer Programming III",
        credits_min=4,
        credits_max=4,
        evidence=evidence,
        parser_name="course_catalog",
        parser_version="1.0",
        authority_tier=AuthorityTier.OFFICIAL_CATALOG,
    )


def test_evidence_quote_must_exist_in_snapshot() -> None:
    report = validate_evidence("Minimum grade 2.5", b"<p>Minimum grade 2.0</p>")

    assert report.accepted is False
    assert report.code == "evidence_not_found"


def test_evidence_validation_matches_normalized_visible_text() -> None:
    report = validate_evidence(
        "CSE 123 Introduction to Computer Programming III",
        b"<h2>CSE 123</h2>\n<p>Introduction to <strong>Computer Programming III</strong></p>",
    )

    assert report.accepted is True
    assert report.code == "exact_evidence_verified"


def test_candidate_without_evidence_is_blocked() -> None:
    report = validate_candidate(_course([]), b"<p>CSE 123</p>")

    assert report.accepted is False
    assert report.issues[0].code == "missing_exact_evidence"
    assert report.issues[0].disposition == "block_publish"


def test_candidate_evidence_must_match_the_named_snapshot() -> None:
    evidence = _evidence("CSE 123", snapshot_id=uuid4())
    report = validate_candidate(
        _course([evidence]),
        {uuid4(): b"<p>CSE 123</p>"},
    )

    assert report.accepted is False
    assert report.issues[0].code == "snapshot_not_available"


def test_structured_table_evidence_verifies_headers_row_and_footnote() -> None:
    snapshot_id = uuid4()
    evidence = _evidence(
        "Mathematics\nName | Score | UW Course\nCalculus BC | 5 | MATH 124",
        snapshot_id=snapshot_id,
    ).model_copy(
        update={
            "table_identifier": "ap-math",
            "row_identifier": "calc-bc",
            "heading_context": "Mathematics",
            "footnote_context": "Credit is subject to duplicate-credit rules.",
        }
    )
    snapshot = b"""
    <section><h3>Mathematics</h3><table id="ap-math">
      <thead><tr><th>Name</th><th>Score</th><th>UW Course</th></tr></thead>
      <tbody><tr id="calc-bc"><td>Calculus BC</td><td>5</td><td>MATH 124</td></tr></tbody>
    </table><p>Credit is subject to duplicate-credit rules.</p></section>
    """

    report = validate_candidate(_course([evidence]), {snapshot_id: snapshot})

    assert report.accepted is True


def test_structured_table_evidence_rejects_invented_cell() -> None:
    snapshot_id = uuid4()
    evidence = _evidence(
        "Mathematics\nName | Score | UW Course\nCalculus BC | 5 | MATH 999",
        snapshot_id=snapshot_id,
    ).model_copy(
        update={
            "table_identifier": "ap-math",
            "row_identifier": "calc-bc",
            "heading_context": "Mathematics",
        }
    )
    snapshot = b"""
    <section><h3>Mathematics</h3><table id="ap-math">
      <thead><tr><th>Name</th><th>Score</th><th>UW Course</th></tr></thead>
      <tbody><tr id="calc-bc"><td>Calculus BC</td><td>5</td><td>MATH 124</td></tr></tbody>
    </table></section>
    """

    report = validate_candidate(_course([evidence]), {snapshot_id: snapshot})

    assert report.accepted is False
    assert report.issues[0].code == "evidence_not_found"
