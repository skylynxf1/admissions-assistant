from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from academic_ingest.models.domain import Course, EffectivePeriod, SourceSnapshot
from academic_ingest.models.enums import MappingOutcome


def test_mapping_not_found_is_not_explicit_no_credit() -> None:
    assert MappingOutcome.NOT_FOUND.value == "not_found"
    assert MappingOutcome.EXPLICIT_NO_CREDIT.value == "explicit_no_credit"
    assert MappingOutcome.NOT_FOUND is not MappingOutcome.EXPLICIT_NO_CREDIT


def test_course_rejects_negative_or_reversed_credits() -> None:
    with pytest.raises(ValidationError, match="credits_min"):
        Course(
            institution_id="uw-seattle",
            campus="Seattle",
            subject="MATH",
            number="124",
            title="Calculus with Analytic Geometry I",
            credits_min=Decimal("-1"),
            credits_max=Decimal("5"),
        )

    with pytest.raises(ValidationError, match="credits_max"):
        Course(
            institution_id="uw-seattle",
            campus="Seattle",
            subject="MATH",
            number="124",
            title="Calculus with Analytic Geometry I",
            credits_min=Decimal("5"),
            credits_max=Decimal("3"),
        )


def test_effective_period_rejects_inverted_dates() -> None:
    with pytest.raises(ValidationError, match="effective_to"):
        EffectivePeriod(
            effective_from=datetime(2026, 9, 1, tzinfo=UTC),
            effective_to=datetime(2026, 1, 1, tzinfo=UTC),
        )


def test_source_snapshot_is_immutable() -> None:
    snapshot = SourceSnapshot(
        source_page_id="11111111-1111-1111-1111-111111111111",
        crawl_job_id="22222222-2222-2222-2222-222222222222",
        raw_content_location="sha256/ab/content.html",
        raw_content_hash="a" * 64,
        normalized_content_hash="b" * 64,
        parser_version="snapshot-v1",
    )

    with pytest.raises(ValidationError, match="frozen"):
        snapshot.raw_content_hash = "c" * 64
