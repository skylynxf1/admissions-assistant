from academic_ingest.prerequisites.ast import NodeType
from academic_ingest.prerequisites.parser import parse_requirement


def test_parser_preserves_nested_and_or_logic() -> None:
    node = parse_requirement("MATH 124 and (CSE 121 or CSE 122), minimum grade 2.0")

    assert node.node_type is NodeType.ALL_OF
    assert node.children[0].normalized_value == "MATH 124"
    assert node.children[1].node_type is NodeType.MINIMUM_GRADE
    assert node.children[1].normalized_value == 2
    assert node.children[1].children[0].node_type is NodeType.ANY_OF
    assert [child.normalized_value for child in node.children[1].children[0].children] == [
        "CSE 121",
        "CSE 122",
    ]


def test_unknown_fragment_becomes_raw_unresolved() -> None:
    node = parse_requirement("CSE 123 and an approved advanced experience")

    unresolved = [child for child in node.walk() if child.node_type is NodeType.RAW_UNRESOLVED]
    assert len(unresolved) == 1
    assert unresolved[0].original_source_text == "an approved advanced experience"
    assert unresolved[0].unresolved_warning is not None


def test_parser_recognizes_concurrency_and_permission_without_overclaiming() -> None:
    node = parse_requirement("CSE 123 may be taken concurrently and permission of instructor")

    assert [child.node_type for child in node.children] == [
        NodeType.CONCURRENT,
        NodeType.PERMISSION,
    ]
    assert node.children[0].children[0].normalized_value == "CSE 123"


def test_parser_recognizes_choose_n_and_either_lists() -> None:
    choose = parse_requirement("choose 2 of MATH 124, MATH 125, MATH 126")
    either = parse_requirement("either CSE 121 or CSE 122")

    assert choose.node_type is NodeType.CHOOSE_N
    assert choose.normalized_value == 2
    assert [child.normalized_value for child in choose.children] == [
        "MATH 124",
        "MATH 125",
        "MATH 126",
    ]
    assert either.node_type is NodeType.ANY_OF
    assert [child.normalized_value for child in either.children] == ["CSE 121", "CSE 122"]


def test_parser_recognizes_sequence_thresholds_and_scope() -> None:
    sequence = parse_requirement("MATH 124 then MATH 125")
    credits = parse_requirement("at least 90 credits")
    campus = parse_requirement("Seattle campus only")

    assert sequence.node_type is NodeType.SEQUENCE
    assert credits.node_type is NodeType.CREDIT_MINIMUM
    assert campus.node_type is NodeType.CAMPUS_RESTRICTION
