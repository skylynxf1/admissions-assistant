from __future__ import annotations

from collections.abc import Iterator
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from academic_ingest.models.enums import ConfidenceTier


class NodeType(StrEnum):
    COURSE = "course"
    ALL_OF = "all_of"
    ANY_OF = "any_of"
    CHOOSE_N = "choose_n"
    SEQUENCE = "sequence"
    MINIMUM_GRADE = "minimum_grade"
    CONCURRENT = "concurrent"
    PLACEMENT = "placement"
    PERMISSION = "permission"
    CLASS_STANDING = "class_standing"
    PROGRAM_RESTRICTION = "program_restriction"
    COLLEGE_RESTRICTION = "college_restriction"
    CAMPUS_RESTRICTION = "campus_restriction"
    CREDIT_MINIMUM = "credit_minimum"
    GPA_MINIMUM = "gpa_minimum"
    CONDITIONAL = "conditional"
    RAW_UNRESOLVED = "raw_unresolved"


COMPOUND_TYPES = {
    NodeType.ALL_OF,
    NodeType.ANY_OF,
    NodeType.CHOOSE_N,
    NodeType.SEQUENCE,
    NodeType.MINIMUM_GRADE,
    NodeType.CONCURRENT,
    NodeType.CONDITIONAL,
}
NUMERIC_TYPES = {
    NodeType.CHOOSE_N,
    NodeType.MINIMUM_GRADE,
    NodeType.CREDIT_MINIMUM,
    NodeType.GPA_MINIMUM,
}


class RequirementNode(BaseModel):
    node_type: NodeType
    children: list[RequirementNode] = Field(default_factory=list)
    normalized_value: str | Decimal | int | dict[str, Any] | None = None
    original_source_text: str
    evidence_record_id: UUID | None = None
    parse_confidence: ConfidenceTier = ConfidenceTier.HIGH_CONFIDENCE
    unresolved_warning: str | None = None

    @model_validator(mode="before")
    @classmethod
    def restore_numeric_json_values(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        node_type = value.get("node_type")
        normalized_value = value.get("normalized_value")
        numeric_values = {node.value for node in NUMERIC_TYPES}
        if node_type in numeric_values and isinstance(normalized_value, str):
            value = dict(value)
            value["normalized_value"] = Decimal(normalized_value)
        return value

    @model_validator(mode="after")
    def validate_shape(self) -> RequirementNode:
        if self.node_type in COMPOUND_TYPES and not self.children:
            raise ValueError(f"{self.node_type.name} node requires child nodes")
        if self.node_type is NodeType.COURSE and not isinstance(self.normalized_value, str):
            raise ValueError("COURSE node requires a normalized course-code value")
        if self.node_type in NUMERIC_TYPES and not isinstance(
            self.normalized_value, (Decimal, int)
        ):
            raise ValueError(f"{self.node_type.name} node requires a numeric value")
        if self.node_type is NodeType.RAW_UNRESOLVED and not self.unresolved_warning:
            raise ValueError("RAW_UNRESOLVED node requires an unresolved warning")
        return self

    def walk(self) -> Iterator[RequirementNode]:
        yield self
        for child in self.children:
            yield from child.walk()

    def to_json(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(cls, raw: str) -> RequirementNode:
        return cls.model_validate_json(raw)

    def render(self) -> str:
        if self.node_type is NodeType.COURSE:
            return str(self.normalized_value)
        if self.node_type in {NodeType.ALL_OF, NodeType.ANY_OF}:
            separator = " and " if self.node_type is NodeType.ALL_OF else " or "
            rendered = separator.join(child.render() for child in self.children)
            return f"({rendered})" if self.node_type is NodeType.ANY_OF else rendered
        if self.node_type is NodeType.CHOOSE_N:
            return f"choose {self.normalized_value} of " + ", ".join(
                child.render() for child in self.children
            )
        if self.node_type is NodeType.SEQUENCE:
            return " then ".join(child.render() for child in self.children)
        if self.node_type is NodeType.MINIMUM_GRADE:
            return (
                f"{self.children[0].render()}, minimum grade {_format_value(self.normalized_value)}"
            )
        if self.node_type is NodeType.CONCURRENT:
            return f"{self.children[0].render()} may be taken concurrently"
        labels = {
            NodeType.PLACEMENT: "placement",
            NodeType.PERMISSION: "permission",
            NodeType.CLASS_STANDING: "class standing",
            NodeType.PROGRAM_RESTRICTION: "program",
            NodeType.COLLEGE_RESTRICTION: "college",
            NodeType.CAMPUS_RESTRICTION: "campus",
            NodeType.CREDIT_MINIMUM: "minimum credits",
            NodeType.GPA_MINIMUM: "minimum GPA",
        }
        if self.node_type in labels:
            return f"{labels[self.node_type]} {_format_value(self.normalized_value)}"
        if self.node_type is NodeType.CONDITIONAL:
            return f"if {_format_value(self.normalized_value)}: {self.children[0].render()}"
        return self.original_source_text


def _format_value(value: object) -> str:
    if isinstance(value, Decimal):
        return format(value, "f")
    return str(value)
