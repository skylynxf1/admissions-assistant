import pytest

from academic_ingest.normalization.identifiers import normalize_course_code
from academic_ingest.normalization.terms import normalize_term


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("  bio   a  201 ", ("BIO A", "201", "BIO A 201")),
        ("MATH& 151", ("MATH&", "151", "MATH& 151")),
        ("cse 123", ("CSE", "123", "CSE 123")),
    ],
)
def test_course_identifiers_preserve_meaningful_subject_spacing(
    source: str, expected: tuple[str, str, str]
) -> None:
    assert normalize_course_code(source) == expected


def test_unknown_course_identifier_is_rejected() -> None:
    with pytest.raises(ValueError, match="course identifier"):
        normalize_course_code("Introduction to Programming")


def test_quarter_term_normalization_is_explicit() -> None:
    assert normalize_term("Autumn 2026") == "2026-autumn"
    assert normalize_term("Fall 2026") == "2026-autumn"
