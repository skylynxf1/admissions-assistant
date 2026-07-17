from __future__ import annotations

from app.eligibility import PrerequisiteEligibilityEvaluator, evaluate_course_eligibility
from app.models import (
    CompletedCourse,
    ConditionType,
    Confidence,
    GroupType,
    PrerequisiteCondition,
    PrerequisiteGroup,
)


def condition(group_id: str, condition_id: str, kind: ConditionType, **updates):
    return PrerequisiteCondition(
        id=condition_id,
        prerequisite_group_id=group_id,
        condition_type=kind,
        confidence=Confidence.HIGH,
        **updates,
    )


def group(group_id: str, kind: GroupType, conditions, minimum_conditions=None):
    return PrerequisiteGroup(
        id=group_id,
        target_course_id="target",
        group_type=kind,
        minimum_conditions=minimum_conditions,
        conditions=conditions,
    )


def evaluate(groups, completed=None, in_progress=None, placement=None, admitted=None):
    return PrerequisiteEligibilityEvaluator(groups).evaluate_course_eligibility(
        "target",
        completed or [],
        in_progress or set(),
        placement or {},
        admitted or set(),
    )


def test_and_prerequisite_group_requires_every_condition():
    groups = [
        group(
            "all",
            GroupType.ALL,
            [
                condition("all", "a", ConditionType.COURSE, prerequisite_course_id="calc1"),
                condition("all", "b", ConditionType.COURSE, prerequisite_course_id="prog1"),
            ],
        )
    ]
    result = evaluate(groups, [CompletedCourse(course_id="calc1")])
    assert result.eligible is False
    assert result.missing_courses == ["prog1"]


def test_or_prerequisite_group_accepts_either_course():
    groups = [
        group(
            "any",
            GroupType.ANY,
            [
                condition("any", "a", ConditionType.COURSE, prerequisite_course_id="calc1"),
                condition("any", "b", ConditionType.COURSE, prerequisite_course_id="stats"),
            ],
        )
    ]
    result = evaluate(groups, [CompletedCourse(course_id="stats")])
    assert result.eligible is True
    assert result.unsatisfied_groups == []


def test_minimum_count_group_enforces_configured_count():
    groups = [
        group(
            "choose-two",
            GroupType.MIN_COUNT,
            [
                condition("choose-two", "a", ConditionType.COURSE, prerequisite_course_id="a"),
                condition("choose-two", "b", ConditionType.COURSE, prerequisite_course_id="b"),
                condition("choose-two", "c", ConditionType.COURSE, prerequisite_course_id="c"),
            ],
            minimum_conditions=2,
        )
    ]
    assert evaluate(groups, [CompletedCourse(course_id="a")]).eligible is False
    assert (
        evaluate(groups, [CompletedCourse(course_id="a"), CompletedCourse(course_id="c")]).eligible
        is True
    )


def test_minimum_grade_requirement_fails_unknown_or_low_grade():
    groups = [
        group(
            "grade",
            GroupType.ALL,
            [
                condition(
                    "grade",
                    "grade-condition",
                    ConditionType.COURSE,
                    prerequisite_course_id="prog1",
                    minimum_grade_points=2.0,
                )
            ],
        )
    ]
    result = evaluate(groups, [CompletedCourse(course_id="prog1", grade_points=1.7)])
    assert result.eligible is False
    assert result.minimum_grade_failures == ["prog1"]


def test_concurrent_enrollment_is_reported_separately():
    groups = [
        group(
            "concurrent",
            GroupType.ALL,
            [
                condition(
                    "concurrent",
                    "concurrent-condition",
                    ConditionType.COURSE,
                    prerequisite_course_id="calc2",
                    may_be_concurrent=True,
                )
            ],
        )
    ]
    result = evaluate(groups, in_progress={"calc2"})
    assert result.eligible is False
    assert result.eligible_with_concurrent_enrollment is True


def test_placement_test_alternative_is_supported_and_explained():
    groups = [
        group(
            "placement",
            GroupType.ANY,
            [
                condition(
                    "placement", "course", ConditionType.COURSE, prerequisite_course_id="calc1"
                ),
                condition(
                    "placement",
                    "test",
                    ConditionType.PLACEMENT,
                    placement_test_code="ALEKS",
                    minimum_placement_score=75,
                ),
            ],
        )
    ]
    failed = evaluate(groups, placement={"ALEKS": 70})
    passed = evaluate(groups, placement={"ALEKS": 80})
    assert failed.placement_alternatives == ["ALEKS >= 75"]
    assert passed.eligible is True


def test_program_admission_and_permission_are_not_assumed():
    groups = [
        group(
            "admission",
            GroupType.ALL,
            [
                condition(
                    "admission",
                    "program",
                    ConditionType.PROGRAM_ADMISSION,
                    admitted_program_id="engineering",
                ),
                condition(
                    "admission",
                    "permission",
                    ConditionType.INSTRUCTOR_PERMISSION,
                    permission_required=True,
                    raw_requirement_text="Instructor permission",
                ),
            ],
        )
    ]
    result = evaluate(groups, admitted={"engineering"})
    assert result.eligible is False
    assert result.permission_requirements == ["Instructor permission"]


def test_complex_course_rule_matches_specification():
    groups = [
        group(
            "math",
            GroupType.ANY,
            [
                condition("math", "calc", ConditionType.COURSE, prerequisite_course_id="calc1"),
                condition(
                    "math",
                    "placement",
                    ConditionType.PLACEMENT,
                    placement_test_code="ALEKS",
                    minimum_placement_score=75,
                ),
            ],
        ),
        group(
            "programming",
            GroupType.ALL,
            [
                condition(
                    "programming",
                    "prog",
                    ConditionType.COURSE,
                    prerequisite_course_id="prog1",
                    minimum_grade_points=2.0,
                )
            ],
        ),
    ]
    result = evaluate_course_eligibility(
        "target",
        [CompletedCourse(course_id="prog1", grade_points=3.0)],
        set(),
        {"ALEKS": 82},
        set(),
        groups,
    )
    assert result.eligible is True
    assert result.satisfied_groups == ["math", "programming"]
