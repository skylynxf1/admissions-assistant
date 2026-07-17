from decimal import Decimal

from academic_ingest.models.domain import ExamCreditRule, TransferPolicy
from academic_ingest.models.enums import MappingOutcome
from academic_ingest.validation.logical import (
    validate_exam_awards,
    validate_mapping_outcome,
    validate_record_logic,
)


def test_exam_awards_reject_mismatched_course_and_credit_cardinality() -> None:
    issues = validate_exam_awards(
        awarded_courses=["MATH 124", "MATH 125"],
        awarded_credit_values=[Decimal("5")],
    )

    assert [issue.code for issue in issues] == ["exam_award_cardinality_mismatch"]


def test_no_mapping_result_never_becomes_explicit_no_credit() -> None:
    issues = validate_mapping_outcome(
        MappingOutcome.EXPLICIT_NO_CREDIT,
        "No matching course was found in the guide.",
    )

    assert [issue.code for issue in issues] == ["unsupported_explicit_no_credit"]


def test_explicit_no_credit_requires_affirmative_source_language() -> None:
    issues = validate_mapping_outcome(
        MappingOutcome.EXPLICIT_NO_CREDIT,
        "No credit is awarded for this examination.",
    )

    assert issues == []


def test_unknown_major_applicability_is_preserved_for_exam_credit() -> None:
    rule = ExamCreditRule(
        institution_id="uw-seattle",
        exam_type="AP",
        exam_name="Calculus BC",
        score_min=5,
        score_max=5,
        awarded_courses=["MATH 124", "MATH 125"],
        awarded_credit_values=[Decimal("5"), Decimal("5")],
        major_specific_applicability="unknown",
    )

    assert validate_record_logic(rule) == []


def test_negative_transfer_credit_limit_is_reported_even_for_unvalidated_input() -> None:
    policy = TransferPolicy.model_construct(
        institution_id="uw-seattle",
        campus="Seattle",
        evidence=[],
        warnings=[],
        unresolved_fields=[],
        parser_name="test",
        parser_version="1",
        crawl_job_id=None,
        authority_tier="official_registrar",
        confidence_tier="unresolved",
        review_status="pending",
        effective_from=None,
        effective_to=None,
        policy_type="lower_division_limit",
        applicant_type="transfer",
        sending_institution_type=None,
        credit_limit=Decimal("-1"),
        course_level=None,
        degree_applicability=None,
        class_standing_effect=None,
        conditions={},
        exceptions=[],
    )

    assert validate_record_logic(policy)[0].code == "negative_credit_limit"
