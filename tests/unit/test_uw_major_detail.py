from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from academic_ingest.adapters.base import AdapterContext
from academic_ingest.adapters.uw.major_detail import MajorDetailAdapter
from academic_ingest.classification.page_classifier import PageClassifier
from academic_ingest.models.domain import Program


def context(fixture: str, url: str) -> AdapterContext:
    html = Path(f"tests/fixtures/uw/html/{fixture}").read_bytes()
    return AdapterContext(
        page=PageClassifier().classify(url, html, content_type="text/html"),
        raw_content=html,
        source_snapshot_id=uuid4(),
        crawl_job_id=uuid4(),
        institution_id="uw-seattle",
        campus="Seattle",
    )


def test_informatics_2026_yields_programming_choice_requirement() -> None:
    result = MajorDetailAdapter().extract(
        context(
            "major_detail_informatics_2026.html",
            "https://admit.washington.edu/majors/informatics/",
        )
    )

    assert len(result.requirements) >= 1
    programming_choice = next(
        item
        for item in result.requirements
        if "CSE 121" in item.allowed_courses and "CSE 122" in item.allowed_courses
    )
    assert programming_choice.minimum_courses == 1


def test_informatics_2026_captures_minimum_grade() -> None:
    result = MajorDetailAdapter().extract(
        context(
            "major_detail_informatics_2026.html",
            "https://admit.washington.edu/majors/informatics/",
        )
    )

    assert any(item.minimum_grade == Decimal("2.0") for item in result.requirements)


def test_informatics_2026_info_200_is_a_required_course() -> None:
    result = MajorDetailAdapter().extract(
        context(
            "major_detail_informatics_2026.html",
            "https://admit.washington.edu/majors/informatics/",
        )
    )

    info_200_requirement = next(
        item for item in result.requirements if "INFO 200" in item.allowed_courses
    )
    assert info_200_requirement.mandatory is True


def test_informatics_2026_requirements_carry_nonempty_evidence() -> None:
    result = MajorDetailAdapter().extract(
        context(
            "major_detail_informatics_2026.html",
            "https://admit.washington.edu/majors/informatics/",
        )
    )

    assert result.requirements
    for requirement in result.requirements:
        assert requirement.evidence
        for evidence in requirement.evidence:
            assert evidence.evidence_text.strip() != ""


def test_computer_science_2026_is_not_informatics_specific() -> None:
    result = MajorDetailAdapter().extract(
        context(
            "major_detail_computer-science_2026.html",
            "https://admit.washington.edu/majors/computer-science/",
        )
    )

    assert len(result.requirements) >= 1


def test_old_fixture_still_parses_and_yields_program() -> None:
    result = MajorDetailAdapter().extract(
        context(
            "major_detail.html",
            "https://admit.washington.edu/majors/informatics/",
        )
    )

    program = next(item for item in result.records if isinstance(item, Program))
    assert program.official_name == "Informatics"
    assert len(result.requirements) >= 1
