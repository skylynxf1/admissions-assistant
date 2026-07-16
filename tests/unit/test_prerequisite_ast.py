from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from academic_ingest.prerequisites.ast import NodeType, RequirementNode


def test_requirement_ast_round_trips_and_renders() -> None:
    evidence_id = uuid4()
    node = RequirementNode(
        node_type=NodeType.ALL_OF,
        children=[
            RequirementNode(
                node_type=NodeType.COURSE,
                normalized_value="MATH 124",
                original_source_text="MATH 124",
                evidence_record_id=evidence_id,
            ),
            RequirementNode(
                node_type=NodeType.GPA_MINIMUM,
                normalized_value=Decimal("2.5"),
                original_source_text="minimum GPA 2.5",
            ),
        ],
        original_source_text="MATH 124 and minimum GPA 2.5",
    )

    restored = RequirementNode.from_json(node.to_json())

    assert restored == node
    assert restored.render() == "MATH 124 and minimum GPA 2.5"
    assert [item.node_type for item in restored.walk()] == [
        NodeType.ALL_OF,
        NodeType.COURSE,
        NodeType.GPA_MINIMUM,
    ]


def test_course_node_requires_a_course_value() -> None:
    with pytest.raises(ValidationError, match="COURSE"):
        RequirementNode(node_type=NodeType.COURSE, original_source_text="missing")
