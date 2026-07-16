from __future__ import annotations

import re
from decimal import Decimal
from uuid import UUID

from academic_ingest.models.enums import ConfidenceTier
from academic_ingest.normalization.identifiers import normalize_course_code
from academic_ingest.prerequisites.ast import NodeType, RequirementNode

COURSE = re.compile(r"^[A-Z][A-Z &]*?\s+\d{3}[A-Z]?$", re.IGNORECASE)
GRADE_MODIFIER = re.compile(r"(?:,\s*)?minimum grade(?: of)?\s+(\d(?:\.\d+)?)\s*$", re.IGNORECASE)


def _balanced_outer_parentheses(text: str) -> bool:
    if not (text.startswith("(") and text.endswith(")")):
        return False
    depth = 0
    for index, character in enumerate(text):
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0 and index != len(text) - 1:
                return False
        if depth < 0:
            return False
    return depth == 0


def _split_top_level(text: str, operator: str) -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    index = 0
    lowered = text.lower()
    while index < len(text):
        character = text[index]
        if character == "(":
            depth += 1
        elif character == ")":
            depth = max(0, depth - 1)
        elif depth == 0 and lowered.startswith(operator, index):
            before = lowered[index - 1] if index else " "
            after_index = index + len(operator)
            after = lowered[after_index] if after_index < len(lowered) else " "
            if not before.isalnum() and not after.isalnum():
                parts.append(text[start:index].strip(" ,;"))
                start = after_index
                index = after_index
                continue
        index += 1
    if parts:
        parts.append(text[start:].strip(" ,;"))
    return [part for part in parts if part]


def _raw_node(text: str, evidence_id: UUID | None) -> RequirementNode:
    return RequirementNode(
        node_type=NodeType.RAW_UNRESOLVED,
        normalized_value=text,
        original_source_text=text,
        evidence_record_id=evidence_id,
        parse_confidence=ConfidenceTier.UNRESOLVED,
        unresolved_warning=(
            "Natural-language fragment was preserved without semantic interpretation"
        ),
    )


def _course_node(text: str, evidence_id: UUID | None) -> RequirementNode:
    _, _, canonical = normalize_course_code(text)
    return RequirementNode(
        node_type=NodeType.COURSE,
        normalized_value=canonical,
        original_source_text=text,
        evidence_record_id=evidence_id,
    )


def _parse_expression(text: str, evidence_id: UUID | None) -> RequirementNode:
    source = text.strip(" ,;")
    while _balanced_outer_parentheses(source):
        source = source[1:-1].strip()

    choose = re.fullmatch(r"choose\s+(\d+)\s+of\s+(.+)", source, re.IGNORECASE)
    if choose:
        choices = [
            part.strip()
            for part in re.split(r",|\bor\b", choose.group(2), flags=re.IGNORECASE)
            if part.strip()
        ]
        return RequirementNode(
            node_type=NodeType.CHOOSE_N,
            children=[_parse_expression(part, evidence_id) for part in choices],
            normalized_value=int(choose.group(1)),
            original_source_text=source,
            evidence_record_id=evidence_id,
        )
    if source.lower().startswith(("either ", "one of ")):
        choices_source = re.sub(r"^(?:either|one of)\s+", "", source, flags=re.IGNORECASE)
        choices = [
            part.strip()
            for part in re.split(r",|\bor\b", choices_source, flags=re.IGNORECASE)
            if part.strip()
        ]
        if len(choices) > 1:
            return RequirementNode(
                node_type=NodeType.ANY_OF,
                children=[_parse_expression(part, evidence_id) for part in choices],
                original_source_text=source,
                evidence_record_id=evidence_id,
            )
    alternatives = _split_top_level(source, "or")
    if alternatives:
        return RequirementNode(
            node_type=NodeType.ANY_OF,
            children=[_parse_expression(part, evidence_id) for part in alternatives],
            original_source_text=source,
            evidence_record_id=evidence_id,
        )
    conjunctions = _split_top_level(source, "and")
    if conjunctions:
        return RequirementNode(
            node_type=NodeType.ALL_OF,
            children=[_parse_expression(part, evidence_id) for part in conjunctions],
            original_source_text=source,
            evidence_record_id=evidence_id,
        )
    sequence = _split_top_level(source, "then")
    if sequence:
        return RequirementNode(
            node_type=NodeType.SEQUENCE,
            children=[_parse_expression(part, evidence_id) for part in sequence],
            original_source_text=source,
            evidence_record_id=evidence_id,
        )

    concurrency = re.fullmatch(r"(.+?)\s+may be taken concurrently", source, re.IGNORECASE)
    if concurrency:
        return RequirementNode(
            node_type=NodeType.CONCURRENT,
            children=[_parse_expression(concurrency.group(1), evidence_id)],
            original_source_text=source,
            evidence_record_id=evidence_id,
        )
    if re.search(r"\bpermission\b", source, re.IGNORECASE):
        return RequirementNode(
            node_type=NodeType.PERMISSION,
            normalized_value=source,
            original_source_text=source,
            evidence_record_id=evidence_id,
        )
    standing = re.search(r"\b(first-year|sophomore|junior|senior) standing\b", source, re.I)
    if standing:
        return RequirementNode(
            node_type=NodeType.CLASS_STANDING,
            normalized_value=standing.group(1).lower(),
            original_source_text=source,
            evidence_record_id=evidence_id,
        )
    minimum_gpa = re.search(r"minimum\s+(?:cumulative\s+)?GPA(?: of)?\s+(\d\.\d+)", source, re.I)
    if minimum_gpa:
        return RequirementNode(
            node_type=NodeType.GPA_MINIMUM,
            normalized_value=Decimal(minimum_gpa.group(1)),
            original_source_text=source,
            evidence_record_id=evidence_id,
        )
    minimum_credits = re.search(r"(?:at least|minimum of)\s+(\d+)\s+credits", source, re.I)
    if minimum_credits:
        return RequirementNode(
            node_type=NodeType.CREDIT_MINIMUM,
            normalized_value=int(minimum_credits.group(1)),
            original_source_text=source,
            evidence_record_id=evidence_id,
        )
    restriction_patterns = (
        (NodeType.CAMPUS_RESTRICTION, r"\b(Seattle|Bothell|Tacoma) campus\b"),
        (NodeType.COLLEGE_RESTRICTION, r"(?:college|school) of ([A-Za-z &]+)"),
        (NodeType.PROGRAM_RESTRICTION, r"(?:open only to|restricted to) ([A-Za-z &]+)"),
    )
    for node_type, pattern in restriction_patterns:
        restriction = re.search(pattern, source, re.IGNORECASE)
        if restriction:
            return RequirementNode(
                node_type=node_type,
                normalized_value=" ".join(restriction.group(1).split()),
                original_source_text=source,
                evidence_record_id=evidence_id,
            )
    if "placement" in source.lower():
        return RequirementNode(
            node_type=NodeType.PLACEMENT,
            normalized_value=source,
            original_source_text=source,
            evidence_record_id=evidence_id,
        )
    if source.lower().startswith("if "):
        condition, separator, consequence = source.partition(",")
        child = (
            _parse_expression(consequence, evidence_id)
            if separator
            else _raw_node(source, evidence_id)
        )
        return RequirementNode(
            node_type=NodeType.CONDITIONAL,
            children=[child],
            normalized_value=condition.removeprefix("if ").strip(),
            original_source_text=source,
            evidence_record_id=evidence_id,
            parse_confidence=ConfidenceTier.NEEDS_REVIEW,
        )
    if COURSE.fullmatch(source):
        return _course_node(source, evidence_id)
    return _raw_node(source, evidence_id)


def parse_requirement(text: str, evidence_id: UUID | None = None) -> RequirementNode:
    source = " ".join(text.split())
    if not source:
        return _raw_node("<empty requirement>", evidence_id)
    grade_match = GRADE_MODIFIER.search(source)
    if grade_match is None:
        return _parse_expression(source, evidence_id)
    base_text = source[: grade_match.start()].rstrip(" ,")
    base = _parse_expression(base_text, evidence_id)
    grade_node = RequirementNode(
        node_type=NodeType.MINIMUM_GRADE,
        children=[base.children[-1] if base.node_type is NodeType.ALL_OF else base],
        normalized_value=Decimal(grade_match.group(1)),
        original_source_text=grade_match.group(0).strip(" ,"),
        evidence_record_id=evidence_id,
    )
    if base.node_type is NodeType.ALL_OF:
        base.children[-1] = grade_node
        base.original_source_text = source
        return base
    grade_node.original_source_text = source
    return grade_node
