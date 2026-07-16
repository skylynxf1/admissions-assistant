from pathlib import Path
from uuid import uuid4

from academic_ingest.adapters.base import AdapterContext
from academic_ingest.adapters.uw.ap_credit import APCreditAdapter
from academic_ingest.classification.page_classifier import PageClassifier


def ap_context() -> AdapterContext:
    html = Path("tests/fixtures/uw/html/ap_credit.html").read_bytes()
    url = "https://admit.washington.edu/apply/transfer/exams-for-credit/ap/"
    return AdapterContext(
        page=PageClassifier().classify(url, html, content_type="text/html"),
        raw_content=html,
        source_snapshot_id=uuid4(),
        crawl_job_id=uuid4(),
        institution_id="uw-seattle",
        campus="Seattle",
    )


def test_ap_score_band_aligns_multiple_awards() -> None:
    result = APCreditAdapter().extract(ap_context())
    rule = next(
        item for item in result.records if item.exam_name == "Calculus BC" and item.score_min == 5
    )

    assert rule.score_max == 5
    assert rule.awarded_courses == ["MATH 124", "MATH 125"]
    assert rule.awarded_credit_values == [5, 5]
    assert rule.general_education_designators == ["NSc", "RSN"]
    assert rule.major_specific_applicability == "unknown"


def test_ap_rowspan_inherits_exam_name_and_score_band() -> None:
    result = APCreditAdapter().extract(ap_context())
    rule = next(
        item for item in result.records if item.exam_name == "Calculus BC" and item.score_min == 3
    )

    assert rule.score_max == 4
    assert rule.awarded_courses == ["MATH 124"]
    assert rule.evidence[0].row_identifier == "calc-bc-3"


def test_ap_placement_only_and_native_speaker_rules_are_preserved() -> None:
    result = APCreditAdapter().extract(ap_context())
    placement = next(item for item in result.records if item.exam_name == "Calculus AB")
    arabic = next(item for item in result.records if item.exam_name == "Arabic Language")

    assert placement.awarded_courses == []
    assert placement.awarded_credit_values == []
    assert placement.placement_effect == "Placement into MATH 112 or MATH 124"
    assert "placement only" in placement.notes[0].lower()
    assert arabic.native_speaker_rule == "NOTE: No credit for native speakers of Arabic."
    assert arabic.duplicate_credit_rule is not None


def test_mismatched_award_cardinality_routes_to_review() -> None:
    result = APCreditAdapter().extract(ap_context())

    assert all(item.exam_name != "Broken Exam" for item in result.records)
    assert any(task.reason == "exam_award_cardinality" for task in result.review_tasks)
