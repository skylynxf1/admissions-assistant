from __future__ import annotations

import pytest
from app.models import (
    Confidence,
    Course,
    CourseOffering,
    CourseRecommendationFeatures,
    GeneralEducationMapping,
    OfferingStatus,
    RecommendationRequest,
    RecommendationWeightConfig,
    StudentCourse,
    StudentCourseStatus,
)
from app.repository import InMemoryRecommendationRepository
from app.sample_data import BC, SCENARIO_ID, UW
from app.scoring import WeightedRecommendationScorer, usefulness_label
from app.service import RecommendationService, scenario_fingerprint


async def response_for(dataset, **request_updates):
    repository = InMemoryRecommendationRepository({SCENARIO_ID: dataset})
    request = RecommendationRequest(
        target_term=request_updates.pop("target_term", "autumn-2026"),
        max_results=request_updates.pop("max_results", 10),
        include_uncertain=request_updates.pop("include_uncertain", True),
        **request_updates,
    )
    return await RecommendationService(repository).recommend(SCENARIO_ID, request)


def recommendation(response, course_id):
    return next(item for item in response.recommendations if item.course_id == course_id)


def feature(**updates):
    values = dict(
        course_id="candidate",
        selected_programs_helped=1,
        selected_institutions_helped=1,
        requirements_satisfied=["Requirement"],
        general_education_categories_satisfied=[],
        directly_unlocked_courses=[],
        descendant_courses_unlocked=[],
        required_descendants_unlocked=[],
        dependency_depth_reduction=0,
        estimated_graduation_terms_saved=0,
        offered_infrequently=False,
        equivalency_confidence="high",
        duplicate_credit_risk=False,
        dead_end_risk=0.2,
        scenario_priorities_helped=[1],
    )
    values.update(updates)
    return CourseRecommendationFeatures(**values)


@pytest.mark.asyncio
async def test_course_helping_multiple_majors_is_identified(dataset):
    response = await response_for(dataset)
    calc2 = recommendation(response, "calc2")
    assert calc2.features.selected_programs_helped == 3
    assert calc2.usefulness_label == "MULTI_PLAN_USEFUL"


@pytest.mark.asyncio
async def test_course_helping_multiple_universities_keeps_outcomes_separate(dataset):
    calc2 = recommendation(await response_for(dataset), "calc2")
    assert calc2.features.selected_institutions_helped == 2
    assert calc2.features.university_coverage[UW] == [
        "DIRECT_EQUIVALENT",
        "GENERAL_EDUCATION",
        "PREREQUISITE_APPLICABLE",
    ]


@pytest.mark.asyncio
async def test_course_satisfying_major_and_general_education_gets_dual_value(dataset):
    calc2 = recommendation(await response_for(dataset), "calc2")
    assert calc2.features.requirements_satisfied
    assert calc2.features.general_education_categories_satisfied == ["NSc", "QR"]
    assert calc2.score_breakdown["dual_requirement_score"] > 0


@pytest.mark.asyncio
async def test_infrequently_offered_course_is_flagged(dataset):
    writing = recommendation(await response_for(dataset), "writing")
    assert writing.features.offered_infrequently is True
    assert writing.score_breakdown["infrequent_offering_score"] > 0


@pytest.mark.asyncio
async def test_unknown_equivalency_is_not_counted_and_can_be_excluded(dataset):
    dataset.equivalencies = [
        item.model_copy(update={"confidence": Confidence.UNKNOWN})
        if item.source_course_id == "calc2"
        else item
        for item in dataset.equivalencies
    ]
    response = await response_for(dataset, include_uncertain=False)
    assert "calc2" not in {item.course_id for item in response.recommendations}
    excluded = next(item for item in response.excluded_courses if item.course_id == "calc2")
    assert "uncertain" in excluded.reason.lower()


@pytest.mark.asyncio
async def test_duplicate_credit_risk_excludes_candidate(dataset):
    dataset.student_courses.append(
        StudentCourse(
            id="completed-target",
            course_id="uw-calc2",
            institution_id=UW,
            course_code_raw="MATH 125",
            credits_earned=5,
            status=StudentCourseStatus.COMPLETED,
        )
    )
    response = await response_for(dataset)
    excluded = next(item for item in response.excluded_courses if item.course_id == "calc2")
    assert "duplicate credit" in excluded.reason.lower()


def test_low_portability_course_uses_nonjudgmental_label():
    features = feature(
        selected_programs_helped=1,
        selected_institutions_helped=0,
        dead_end_risk=0.8,
        scenario_priorities_helped=[3],
    )
    assert usefulness_label(features) == "LOW_PORTABILITY"


def test_priority_weighted_programs_change_major_coverage_score():
    scorer = WeightedRecommendationScorer()
    config = RecommendationWeightConfig()
    high = scorer.score(
        feature(scenario_priorities_helped=[1]),
        config,
        all_program_priorities=[1, 3],
        selected_institution_count=2,
    )
    low = scorer.score(
        feature(scenario_priorities_helped=[3]),
        config,
        all_program_priorities=[1, 3],
        selected_institution_count=2,
    )
    assert high.breakdown["major_coverage_score"] > low.breakdown["major_coverage_score"]


@pytest.mark.asyncio
async def test_completed_course_is_excluded(dataset):
    response = await response_for(dataset)
    excluded = next(item for item in response.excluded_courses if item.course_id == "calc1")
    assert excluded.reason == "Course is already completed."


@pytest.mark.asyncio
async def test_target_term_offering_exclusion(dataset):
    response = await response_for(dataset, target_term="autumn-2026")
    excluded = next(item for item in response.excluded_courses if item.course_id == "linear")
    assert "No confirmed or typical offering" in excluded.reason


@pytest.mark.asyncio
async def test_course_with_no_offering_data_is_not_excluded(dataset):
    # No offering rows exist for this course at all: availability is genuinely
    # unknown, not confirmed absent, so it must remain a candidate.
    dataset.courses.append(
        Course(
            id="unscheduled",
            institution_id=BC,
            course_code="PHIL 101",
            title="Intro to Philosophy",
            credits_min=5,
            confidence=Confidence.HIGH,
        )
    )
    dataset.general_education_mappings.append(
        GeneralEducationMapping(
            id="ge-unscheduled-uw",
            course_id="unscheduled",
            institution_id=UW,
            category_code="HUM",
            category_name="Humanities",
            status="CONFIRMED",
            confidence=Confidence.HIGH,
        )
    )
    response = await response_for(dataset, target_term="autumn-2026")
    assert "unscheduled" not in {item.course_id for item in response.excluded_courses}
    rec = recommendation(response, "unscheduled")
    assert any(
        "availability" in warning.lower() and "unknown" in warning.lower()
        for warning in rec.warnings
    )


@pytest.mark.asyncio
async def test_course_with_explicit_not_offered_evidence_is_still_excluded(dataset):
    # Offering data exists and explicitly says NOT_OFFERED for the target term:
    # this is real evidence of non-availability, so exclusion remains correct.
    dataset.courses.append(
        Course(
            id="never-scheduled",
            institution_id=BC,
            course_code="PHIL 102",
            title="Ethics",
            credits_min=5,
            confidence=Confidence.HIGH,
        )
    )
    dataset.general_education_mappings.append(
        GeneralEducationMapping(
            id="ge-never-scheduled-uw",
            course_id="never-scheduled",
            institution_id=UW,
            category_code="HUM",
            category_name="Humanities",
            status="CONFIRMED",
            confidence=Confidence.HIGH,
        )
    )
    dataset.offerings.append(
        CourseOffering(
            id="offering-never-scheduled-autumn-2026",
            course_id="never-scheduled",
            academic_year=2026,
            term_name="autumn-2026",
            offering_status=OfferingStatus.NOT_OFFERED,
        )
    )
    response = await response_for(dataset, target_term="autumn-2026")
    excluded = next(
        item for item in response.excluded_courses if item.course_id == "never-scheduled"
    )
    assert "No confirmed or typical offering" in excluded.reason
    assert "never-scheduled" not in {item.course_id for item in response.recommendations}


@pytest.mark.asyncio
async def test_course_confirmed_offered_in_term_is_unaffected(dataset):
    response = await response_for(dataset, target_term="autumn-2026")
    calc2 = recommendation(response, "calc2")
    assert not any("schedule/offering data" in warning.lower() for warning in calc2.warnings)


def test_deterministic_score_calculation_has_complete_breakdown():
    scorer = WeightedRecommendationScorer()
    config = RecommendationWeightConfig()
    features = feature(
        selected_programs_helped=2,
        selected_institutions_helped=2,
        directly_unlocked_courses=["a", "b"],
        required_descendants_unlocked=["c", "d", "e"],
        general_education_categories_satisfied=["QR"],
        estimated_graduation_terms_saved=1,
    )
    first = scorer.score(
        features, config, all_program_priorities=[1, 2], selected_institution_count=2
    )
    second = scorer.score(
        features, config, all_program_priorities=[1, 2], selected_institution_count=2
    )
    assert first == second
    assert set(first.breakdown) == {
        "major_coverage_score",
        "university_coverage_score",
        "unlock_score",
        "dual_requirement_score",
        "graduation_acceleration_score",
        "infrequent_offering_score",
        "uncertain_equivalency_penalty",
        "dead_end_penalty",
        "duplicate_credit_penalty",
    }


@pytest.mark.asyncio
async def test_stable_recommendation_ordering(dataset):
    first = await response_for(dataset.model_copy(deep=True))
    second = await response_for(dataset.model_copy(deep=True))
    assert [(item.course_id, item.score) for item in first.recommendations] == [
        (item.course_id, item.score) for item in second.recommendations
    ]
    assert [item.rank for item in first.recommendations] == list(
        range(1, len(first.recommendations) + 1)
    )


def test_scenario_fingerprint_changes_with_academic_inputs(dataset):
    request = RecommendationRequest(target_term="autumn-2026")
    original = scenario_fingerprint(dataset, request)
    dataset.scenario = dataset.scenario.model_copy(update={"max_credits": 10})
    assert scenario_fingerprint(dataset, request) != original
