"""Tests for the deterministic UW Bellevue College equivalency-guide parser.

These run entirely offline against the saved fixture
`tests/fixtures/uw/html/equivalency_guide_bellevue_2026.html` (the live guide,
retrieved 2026-07-21). No network calls, no invented rows: every assertion below
either checks the parser's structural behavior or quotes a real row found in the
fixture.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from academic_ingest.adapters.uw.bellevue_equivalency import (
    ParseResult,
    parse_bellevue_equivalencies,
)
from academic_ingest.models.transfer_state import SUPABASE_MAPPING_TYPE_TO_STATE

_FIXTURE_PATH = Path("tests/fixtures/uw/html/equivalency_guide_bellevue_2026.html")
_SOURCE_URL = "https://admit.washington.edu/apply/transfer/equivalency-guide/bellevue/"


@lru_cache(maxsize=1)
def _parsed() -> ParseResult:
    html = _FIXTURE_PATH.read_text(encoding="utf-8")
    return parse_bellevue_equivalencies(html, source_url=_SOURCE_URL)


def test_parsing_the_fixture_returns_many_records_with_no_exceptions() -> None:
    result = _parsed()
    assert len(result.records) > 300


def test_obsolete_rows_are_excluded() -> None:
    result = _parsed()
    assert result.skipped["obsolete"] >= 800


def test_cross_reference_rows_are_excluded() -> None:
    result = _parsed()
    assert result.skipped["cross_reference"] >= 1

    all_codes = [record.source_course_codes for record in result.records]
    assert ["ACCT& 202"] not in all_codes


def test_conditional_row_lands_in_review_not_records() -> None:
    result = _parsed()

    conditional_reviews = [row for row in result.review_rows if row.reason == "conditional"]
    assert conditional_reviews
    accounting_review = next(
        row for row in conditional_reviews if row.source_cell.startswith("ACCT& 201, 202")
    )
    assert "otherwise" in accounting_review.destination_cell.lower()

    all_codes = [record.source_course_codes for record in result.records]
    assert ["ACCT& 201", "ACCT& 202"] not in all_codes


def test_every_record_has_required_fields() -> None:
    result = _parsed()
    assert result.records, "expected at least one record to check"
    for record in result.records:
        assert record.source_course_codes
        assert record.evidence_refs
        assert record.mapping_type in SUPABASE_MAPPING_TYPE_TO_STATE


def test_known_simple_row_parses_to_direct_equivalent() -> None:
    # Real row from the fixture: "ACCT& 203 (5) formerly ACCTG 230 (5)" -> "ACCTG 225 (5)"
    result = _parsed()
    record = next(
        record for record in result.records if record.source_course_codes == ["ACCT& 203"]
    )
    assert record.mapping_type == "direct_equivalent"
    assert record.destination_outcome == "ACCTG 225 (5)"
    assert record.credits_awarded == 5.0


def test_no_credit_row_yields_no_credit_mapping_type() -> None:
    # Real row from the fixture: "BUS 145 (5) formerly G BUS 145" -> "No credit"
    result = _parsed()
    record = next(record for record in result.records if record.source_course_codes == ["BUS 145"])
    assert record.mapping_type == "no_credit"
    assert record.destination_outcome == "No credit"
