from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from academic_ingest.adapters.base import AdapterContext
from academic_ingest.adapters.uw.course_catalog import CourseCatalogAdapter
from academic_ingest.adapters.uw.course_glossary import CourseGlossaryAdapter
from academic_ingest.classification.page_classifier import PageClassifier


def course_context(name: str, url: str, *, selected: set[str] | None = None) -> AdapterContext:
    html = Path(f"tests/fixtures/uw/html/{name}").read_bytes()
    return AdapterContext(
        page=PageClassifier().classify(url, html, content_type="text/html"),
        raw_content=html,
        source_snapshot_id=uuid4(),
        crawl_job_id=uuid4(),
        institution_id="uw-seattle",
        campus="Seattle",
        selected_course_codes=selected,
    )


def test_course_adapter_preserves_block_and_credit_range() -> None:
    context = course_context(
        "courses_cse.html",
        "https://www.washington.edu/students/crscat/cse.html",
    )

    result = CourseCatalogAdapter().extract(context)
    course = next(item for item in result.records if item.canonical_code == "CSE 4XX")

    assert (course.credits_min, course.credits_max) == (Decimal(3), Decimal(5))
    assert course.evidence[0].css_selector == "#cse4xx"
    assert "Prerequisite:" in course.evidence[0].evidence_text
    assert course.prerequisite_text == "CSE 143 and INFO 200."
    assert course.historical_offering_notes == ["jointly with INFO 4XX."]


def test_course_adapter_extracts_semantics_without_losing_evidence() -> None:
    context = course_context(
        "courses_cse.html",
        "https://www.washington.edu/students/crscat/cse.html",
    )

    result = CourseCatalogAdapter().extract(context)
    course = next(item for item in result.records if item.canonical_code == "CSE 143")

    assert course.general_education_designators == ["NSc", "RSN"]
    assert course.equivalent_courses == ["CSS 143", "TCSS 143"]
    assert course.overlapping_courses == ["CSE 122", "CSE 123", "T INFO 473"]
    assert course.prerequisite_text == "CSE 142."
    assert course.historical_offering_notes == ["AWSpS."]
    assert "View course details in MyPlan" in course.evidence[0].evidence_text


def test_unknown_credit_course_routes_to_review() -> None:
    result = CourseCatalogAdapter().extract(
        course_context(
            "courses_cse.html",
            "https://www.washington.edu/students/crscat/cse.html",
        )
    )

    assert all(item.canonical_code != "CSE 399" for item in result.records)
    assert any("CSE 399" in task.unresolved_question for task in result.review_tasks)


def test_selected_course_filter_is_exact() -> None:
    selected = {"MATH 124", "MATH 125", "MATH 126", "STAT 311", "ENGL 131"}
    result = CourseCatalogAdapter().extract(
        course_context(
            "courses_selected.html",
            "https://www.washington.edu/students/crscat/math.html",
            selected=selected,
        )
    )

    assert {item.canonical_code for item in result.records} == selected


def test_catalog_index_discovers_only_canonical_subject_pages() -> None:
    html = b"""
    <title>Seattle course descriptions</title>
    <a href="cse.html">CSE</a>
    <a href="info.html">INFO</a>
    <a href="glossary.html">Glossary</a>
    <a href="https://www.uwb.edu/catalog">Bothell</a>
    """
    context = AdapterContext(
        page=PageClassifier().classify(
            "https://www.washington.edu/students/crscat/",
            html,
            content_type="text/html",
        ),
        raw_content=html,
        source_snapshot_id=uuid4(),
        crawl_job_id=uuid4(),
        institution_id="uw-seattle",
        campus="Seattle",
    )

    result = CourseCatalogAdapter().extract(context)

    assert result.discovered_links == [
        "https://www.washington.edu/students/crscat/cse.html",
        "https://www.washington.edu/students/crscat/info.html",
    ]


def test_course_glossary_is_extracted_with_versioned_evidence() -> None:
    html = Path("tests/fixtures/uw/html/course_glossary.html").read_bytes()
    context = AdapterContext(
        page=PageClassifier().classify(
            "https://www.washington.edu/students/crscat/glossary.html",
            html,
            content_type="text/html",
        ),
        raw_content=html,
        source_snapshot_id=uuid4(),
        crawl_job_id=uuid4(),
        institution_id="uw-seattle",
        campus="Seattle",
    )

    result = CourseGlossaryAdapter().extract(context)

    assert [entry.term for entry in result.records] == ["Credits", "Offered"]
    assert result.records[0].evidence.source_snapshot_id == context.source_snapshot_id
