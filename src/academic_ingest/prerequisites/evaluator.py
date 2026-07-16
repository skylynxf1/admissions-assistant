from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field

from academic_ingest.prerequisites.ast import NodeType, RequirementNode


class EvaluationStatus(StrEnum):
    SATISFIED = "satisfied"
    UNSATISFIED = "unsatisfied"
    UNRESOLVED = "unresolved"


class CourseCompletion(BaseModel):
    grade: Decimal | None = Field(default=None, ge=0, le=4)
    sequence_index: int | None = Field(default=None, ge=0)


class SyntheticTranscript(BaseModel):
    completed_courses: dict[str, CourseCompletion] = Field(default_factory=dict)
    concurrent_courses: set[str] = Field(default_factory=set)
    placements: set[str] = Field(default_factory=set)
    permissions: set[str] = Field(default_factory=set)
    class_standing: str | None = None
    program: str | None = None
    college: str | None = None
    campus: str | None = None
    total_credits: Decimal | None = Field(default=None, ge=0)
    gpa: Decimal | None = Field(default=None, ge=0, le=4)
    conditions: set[str] = Field(default_factory=set)


class EvaluationResult(BaseModel):
    status: EvaluationStatus
    reasons: list[str] = Field(default_factory=list)
    unresolved_fragments: list[str] = Field(default_factory=list)


def _result(
    status: EvaluationStatus,
    reason: str,
    *,
    unresolved: str | None = None,
) -> EvaluationResult:
    return EvaluationResult(
        status=status,
        reasons=[reason],
        unresolved_fragments=[unresolved] if unresolved else [],
    )


def _combine_all(results: list[EvaluationResult]) -> EvaluationResult:
    if any(result.status is EvaluationStatus.UNSATISFIED for result in results):
        status = EvaluationStatus.UNSATISFIED
    elif any(result.status is EvaluationStatus.UNRESOLVED for result in results):
        status = EvaluationStatus.UNRESOLVED
    else:
        status = EvaluationStatus.SATISFIED
    return EvaluationResult(
        status=status,
        reasons=[reason for result in results for reason in result.reasons],
        unresolved_fragments=[
            fragment for result in results for fragment in result.unresolved_fragments
        ],
    )


def _combine_any(results: list[EvaluationResult]) -> EvaluationResult:
    if any(result.status is EvaluationStatus.SATISFIED for result in results):
        status = EvaluationStatus.SATISFIED
    elif any(result.status is EvaluationStatus.UNRESOLVED for result in results):
        status = EvaluationStatus.UNRESOLVED
    else:
        status = EvaluationStatus.UNSATISFIED
    return EvaluationResult(
        status=status,
        reasons=[reason for result in results for reason in result.reasons],
        unresolved_fragments=[
            fragment for result in results for fragment in result.unresolved_fragments
        ],
    )


def _numeric(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    raise TypeError(f"expected numeric requirement value, received {value!r}")


def _evaluate_minimum_grade(
    node: RequirementNode, transcript: SyntheticTranscript, minimum: Decimal
) -> EvaluationResult:
    if node.node_type is NodeType.COURSE:
        code = str(node.normalized_value)
        completion = transcript.completed_courses.get(code)
        if completion is None:
            return _result(EvaluationStatus.UNSATISFIED, f"{code} is not completed")
        if completion.grade is None:
            return _result(
                EvaluationStatus.UNRESOLVED,
                f"{code} has no grade available for minimum {minimum}",
                unresolved=code,
            )
        if completion.grade >= minimum:
            return _result(
                EvaluationStatus.SATISFIED,
                f"{code} grade {completion.grade} meets minimum {minimum}",
            )
        return _result(
            EvaluationStatus.UNSATISFIED,
            f"{code} grade {completion.grade} is below minimum {minimum}",
        )
    children = [_evaluate_minimum_grade(child, transcript, minimum) for child in node.children]
    if node.node_type is NodeType.ANY_OF:
        return _combine_any(children)
    if node.node_type in {NodeType.ALL_OF, NodeType.SEQUENCE}:
        return _combine_all(children)
    return _result(
        EvaluationStatus.UNRESOLVED,
        f"Minimum-grade logic cannot be applied to {node.node_type.value}",
        unresolved=node.original_source_text,
    )


def evaluate(node: RequirementNode, transcript: SyntheticTranscript) -> EvaluationResult:
    if node.node_type is NodeType.COURSE:
        code = str(node.normalized_value)
        if code in transcript.completed_courses:
            return _result(EvaluationStatus.SATISFIED, f"{code} is completed")
        return _result(EvaluationStatus.UNSATISFIED, f"{code} is not completed")
    if node.node_type is NodeType.ALL_OF:
        return _combine_all([evaluate(child, transcript) for child in node.children])
    if node.node_type is NodeType.ANY_OF:
        return _combine_any([evaluate(child, transcript) for child in node.children])
    if node.node_type is NodeType.CHOOSE_N:
        results = [evaluate(child, transcript) for child in node.children]
        required = int(_numeric(node.normalized_value))
        satisfied = sum(result.status is EvaluationStatus.SATISFIED for result in results)
        unresolved = sum(result.status is EvaluationStatus.UNRESOLVED for result in results)
        if satisfied >= required:
            status = EvaluationStatus.SATISFIED
        elif satisfied + unresolved < required:
            status = EvaluationStatus.UNSATISFIED
        else:
            status = EvaluationStatus.UNRESOLVED
        return EvaluationResult(
            status=status,
            reasons=[reason for result in results for reason in result.reasons],
            unresolved_fragments=[
                fragment for result in results for fragment in result.unresolved_fragments
            ],
        )
    if node.node_type is NodeType.MINIMUM_GRADE:
        return _evaluate_minimum_grade(
            node.children[0], transcript, _numeric(node.normalized_value)
        )
    if node.node_type is NodeType.CONCURRENT:
        child = node.children[0]
        if child.node_type is not NodeType.COURSE:
            return _result(
                EvaluationStatus.UNRESOLVED,
                "Concurrent requirement is not a course",
                unresolved=node.original_source_text,
            )
        code = str(child.normalized_value)
        if code in transcript.completed_courses or code in transcript.concurrent_courses:
            return _result(EvaluationStatus.SATISFIED, f"{code} is completed or concurrent")
        return _result(EvaluationStatus.UNSATISFIED, f"{code} is neither completed nor concurrent")
    if node.node_type is NodeType.SEQUENCE:
        results = [evaluate(child, transcript) for child in node.children]
        combined = _combine_all(results)
        if combined.status is not EvaluationStatus.SATISFIED:
            return combined
        indices = [
            transcript.completed_courses[str(child.normalized_value)].sequence_index
            for child in node.children
            if child.node_type is NodeType.COURSE
        ]
        if len(indices) != len(node.children) or any(index is None for index in indices):
            return _result(
                EvaluationStatus.UNRESOLVED,
                "Course order is unavailable for sequence evaluation",
                unresolved=node.original_source_text,
            )
        resolved_indices = [index for index in indices if index is not None]
        status = (
            EvaluationStatus.SATISFIED
            if resolved_indices == sorted(resolved_indices)
            else EvaluationStatus.UNSATISFIED
        )
        return _result(status, f"Sequence order is {resolved_indices}")
    if node.node_type is NodeType.PLACEMENT:
        value = str(node.normalized_value)
        status = (
            EvaluationStatus.SATISFIED
            if value in transcript.placements
            else EvaluationStatus.UNSATISFIED
        )
        return _result(status, f"Placement requirement: {value}")
    if node.node_type is NodeType.PERMISSION:
        value = str(node.normalized_value)
        status = (
            EvaluationStatus.SATISFIED
            if value in transcript.permissions
            else EvaluationStatus.UNSATISFIED
        )
        return _result(status, f"Permission requirement: {value}")
    if node.node_type is NodeType.CLASS_STANDING:
        if transcript.class_standing is None:
            return _result(
                EvaluationStatus.UNRESOLVED,
                "Class standing is unavailable",
                unresolved=node.original_source_text,
            )
        order = {"first-year": 0, "sophomore": 1, "junior": 2, "senior": 3}
        required_standing_rank = order.get(str(node.normalized_value).lower())
        actual_standing_rank = order.get(transcript.class_standing.lower())
        if required_standing_rank is None or actual_standing_rank is None:
            return _result(
                EvaluationStatus.UNRESOLVED,
                "Class standing value is not recognized",
                unresolved=node.original_source_text,
            )
        status = (
            EvaluationStatus.SATISFIED
            if actual_standing_rank >= required_standing_rank
            else EvaluationStatus.UNSATISFIED
        )
        return _result(status, f"Class standing is {transcript.class_standing}")
    restriction_fields = {
        NodeType.PROGRAM_RESTRICTION: transcript.program,
        NodeType.COLLEGE_RESTRICTION: transcript.college,
        NodeType.CAMPUS_RESTRICTION: transcript.campus,
    }
    if node.node_type in restriction_fields:
        actual_value = restriction_fields[node.node_type]
        if actual_value is None:
            return _result(
                EvaluationStatus.UNRESOLVED,
                f"{node.node_type.value} value is unavailable",
                unresolved=node.original_source_text,
            )
        status = (
            EvaluationStatus.SATISFIED
            if actual_value.casefold() == str(node.normalized_value).casefold()
            else EvaluationStatus.UNSATISFIED
        )
        return _result(status, f"{node.node_type.value}: {actual_value}")
    if node.node_type in {NodeType.CREDIT_MINIMUM, NodeType.GPA_MINIMUM}:
        actual_numeric = (
            transcript.total_credits
            if node.node_type is NodeType.CREDIT_MINIMUM
            else transcript.gpa
        )
        if actual_numeric is None:
            return _result(
                EvaluationStatus.UNRESOLVED,
                f"{node.node_type.value} value is unavailable",
                unresolved=node.original_source_text,
            )
        minimum = _numeric(node.normalized_value)
        status = (
            EvaluationStatus.SATISFIED
            if actual_numeric >= minimum
            else EvaluationStatus.UNSATISFIED
        )
        return _result(status, f"Observed {actual_numeric}; minimum is {minimum}")
    if node.node_type is NodeType.CONDITIONAL:
        condition = str(node.normalized_value)
        if condition not in transcript.conditions:
            return _result(
                EvaluationStatus.UNRESOLVED,
                f"Conditional predicate is unresolved: {condition}",
                unresolved=node.original_source_text,
            )
        return evaluate(node.children[0], transcript)
    return _result(
        EvaluationStatus.UNRESOLVED,
        node.unresolved_warning or "Requirement fragment is unresolved",
        unresolved=node.original_source_text,
    )
