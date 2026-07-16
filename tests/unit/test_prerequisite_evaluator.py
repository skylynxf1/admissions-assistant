from decimal import Decimal

from academic_ingest.prerequisites.ast import NodeType, RequirementNode
from academic_ingest.prerequisites.evaluator import (
    CourseCompletion,
    EvaluationStatus,
    SyntheticTranscript,
    evaluate,
)
from academic_ingest.prerequisites.parser import parse_requirement


def test_nested_requirement_evaluates_against_grades() -> None:
    node = parse_requirement("MATH 124 and (CSE 121 or CSE 122), minimum grade 2.0")
    transcript = SyntheticTranscript(
        completed_courses={
            "MATH 124": CourseCompletion(grade=Decimal("3.0")),
            "CSE 122": CourseCompletion(grade=Decimal("2.5")),
        }
    )

    result = evaluate(node, transcript)

    assert result.status is EvaluationStatus.SATISFIED


def test_minimum_grade_failure_is_unsatisfied() -> None:
    node = parse_requirement("CSE 122, minimum grade 2.0")
    transcript = SyntheticTranscript(
        completed_courses={"CSE 122": CourseCompletion(grade=Decimal("1.9"))}
    )

    result = evaluate(node, transcript)

    assert result.status is EvaluationStatus.UNSATISFIED
    assert "2.0" in " ".join(result.reasons)


def test_unresolved_source_fragment_stays_unresolved() -> None:
    node = parse_requirement("CSE 123 and an approved advanced experience")
    transcript = SyntheticTranscript(
        completed_courses={"CSE 123": CourseCompletion(grade=Decimal("4.0"))}
    )

    assert evaluate(node, transcript).status is EvaluationStatus.UNRESOLVED


def test_credit_and_campus_constraints_use_three_state_evaluation() -> None:
    node = RequirementNode(
        node_type=NodeType.ALL_OF,
        children=[
            RequirementNode(
                node_type=NodeType.CREDIT_MINIMUM,
                normalized_value=90,
                original_source_text="at least 90 credits",
            ),
            RequirementNode(
                node_type=NodeType.CAMPUS_RESTRICTION,
                normalized_value="Seattle",
                original_source_text="Seattle campus only",
            ),
        ],
        original_source_text="at least 90 credits and Seattle campus only",
    )

    assert (
        evaluate(
            node,
            SyntheticTranscript(total_credits=Decimal(95), campus="Seattle"),
        ).status
        is EvaluationStatus.SATISFIED
    )
    assert evaluate(node, SyntheticTranscript()).status is EvaluationStatus.UNRESOLVED
