from __future__ import annotations

from dataclasses import dataclass, field

from app.models import (
    CompletedCourse,
    ConditionType,
    Confidence,
    CourseEligibilityResult,
    GroupType,
    PrerequisiteCondition,
    PrerequisiteGroup,
)


CONFIDENCE_ORDER = {
    Confidence.HIGH: 3,
    Confidence.MEDIUM: 2,
    Confidence.LOW: 1,
    Confidence.UNKNOWN: 0,
}


@dataclass
class ConditionEvaluation:
    satisfied: bool = False
    concurrent: bool = False
    missing_courses: list[str] = field(default_factory=list)
    minimum_grade_failures: list[str] = field(default_factory=list)
    placement_alternatives: list[str] = field(default_factory=list)
    permission_requirements: list[str] = field(default_factory=list)


class PrerequisiteEligibilityEvaluator:
    def __init__(self, prerequisite_groups: list[PrerequisiteGroup]) -> None:
        self.groups_by_course: dict[str, list[PrerequisiteGroup]] = {}
        for group in prerequisite_groups:
            self.groups_by_course.setdefault(group.target_course_id, []).append(group)
        for groups in self.groups_by_course.values():
            groups.sort(key=lambda value: (value.group_order, value.id))

    def evaluate_course_eligibility(
        self,
        course_id: str,
        completed_courses: list[CompletedCourse],
        in_progress_courses: set[str],
        placement_results: dict[str, float],
        admitted_programs: set[str],
    ) -> CourseEligibilityResult:
        groups = self.groups_by_course.get(course_id, [])
        if not groups:
            return CourseEligibilityResult(
                eligible=True,
                eligible_with_concurrent_enrollment=False,
                confidence=Confidence.HIGH.value,
            )

        completed = {course.course_id: course for course in completed_courses}
        completed_credits = sum(course.credits_earned for course in completed_courses)
        satisfied_groups: list[str] = []
        unsatisfied_groups: list[str] = []
        missing_courses: set[str] = set()
        minimum_grade_failures: set[str] = set()
        placement_alternatives: set[str] = set()
        permission_requirements: set[str] = set()
        required_group_results: list[tuple[bool, bool]] = []
        confidences: list[Confidence] = []

        for group in groups:
            condition_results = [
                self._evaluate_condition(
                    condition,
                    completed,
                    in_progress_courses,
                    placement_results,
                    admitted_programs,
                    completed_credits,
                )
                for condition in group.conditions
            ]
            confidences.extend(condition.confidence for condition in group.conditions)
            satisfied_count = sum(result.satisfied for result in condition_results)
            if group.group_type == GroupType.ALL:
                group_satisfied = bool(condition_results) and satisfied_count == len(condition_results)
            elif group.group_type == GroupType.ANY:
                group_satisfied = satisfied_count >= 1
            else:
                group_satisfied = satisfied_count >= (group.minimum_conditions or 1)
            group_uses_concurrency = group_satisfied and any(result.concurrent for result in condition_results if result.satisfied)

            if group_satisfied:
                satisfied_groups.append(group.id)
            elif group.required:
                unsatisfied_groups.append(group.id)
                for result in condition_results:
                    missing_courses.update(result.missing_courses)
                    minimum_grade_failures.update(result.minimum_grade_failures)
                    placement_alternatives.update(result.placement_alternatives)
                    permission_requirements.update(result.permission_requirements)

            if group.required:
                required_group_results.append((group_satisfied, group_uses_concurrency))

        all_required_satisfied = all(result[0] for result in required_group_results)
        needs_concurrency = all_required_satisfied and any(result[1] for result in required_group_results)
        confidence = min(confidences, key=lambda value: CONFIDENCE_ORDER[value]) if confidences else Confidence.HIGH
        return CourseEligibilityResult(
            eligible=all_required_satisfied and not needs_concurrency,
            eligible_with_concurrent_enrollment=needs_concurrency,
            satisfied_groups=satisfied_groups,
            unsatisfied_groups=unsatisfied_groups,
            missing_courses=sorted(missing_courses),
            minimum_grade_failures=sorted(minimum_grade_failures),
            placement_alternatives=sorted(placement_alternatives),
            permission_requirements=sorted(permission_requirements),
            confidence=confidence.value,
        )

    @staticmethod
    def _evaluate_condition(
        condition: PrerequisiteCondition,
        completed: dict[str, CompletedCourse],
        in_progress: set[str],
        placement_results: dict[str, float],
        admitted_programs: set[str],
        completed_credits: float,
    ) -> ConditionEvaluation:
        result = ConditionEvaluation()
        if condition.condition_type == ConditionType.COURSE and condition.prerequisite_course_id:
            completed_course = completed.get(condition.prerequisite_course_id)
            if completed_course:
                if condition.minimum_grade_points is None:
                    result.satisfied = True
                elif completed_course.grade_points is not None and completed_course.grade_points >= condition.minimum_grade_points:
                    result.satisfied = True
                else:
                    result.minimum_grade_failures.append(condition.prerequisite_course_id)
            elif condition.prerequisite_course_id in in_progress and condition.may_be_concurrent:
                result.satisfied = True
                result.concurrent = True
            else:
                result.missing_courses.append(condition.prerequisite_course_id)
            return result

        if condition.condition_type == ConditionType.PLACEMENT and condition.placement_test_code:
            score = placement_results.get(condition.placement_test_code)
            result.satisfied = score is not None and score >= float(condition.minimum_placement_score or 0)
            if not result.satisfied:
                minimum = condition.minimum_placement_score
                result.placement_alternatives.append(
                    f"{condition.placement_test_code}{f' >= {minimum:g}' if minimum is not None else ''}"
                )
            return result

        if condition.condition_type == ConditionType.CREDIT_COUNT:
            result.satisfied = completed_credits >= float(condition.minimum_credits or 0)
            return result

        if condition.condition_type == ConditionType.PROGRAM_ADMISSION and condition.admitted_program_id:
            result.satisfied = condition.admitted_program_id in admitted_programs
            if not result.satisfied:
                result.permission_requirements.append(f"Admission to program {condition.admitted_program_id}")
            return result

        if condition.condition_type == ConditionType.INSTRUCTOR_PERMISSION:
            result.permission_requirements.append(condition.raw_requirement_text or "Instructor permission required")
            return result

        # OTHER and malformed conditions are never treated as satisfied.
        result.permission_requirements.append(condition.raw_requirement_text or "Unresolved prerequisite condition")
        return result


def evaluate_course_eligibility(
    course_id: str,
    completed_courses: list[CompletedCourse],
    in_progress_courses: set[str],
    placement_results: dict[str, float],
    admitted_programs: set[str],
    prerequisite_groups: list[PrerequisiteGroup],
) -> CourseEligibilityResult:
    return PrerequisiteEligibilityEvaluator(prerequisite_groups).evaluate_course_eligibility(
        course_id,
        completed_courses,
        in_progress_courses,
        placement_results,
        admitted_programs,
    )
