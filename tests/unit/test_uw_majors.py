from pathlib import Path
from uuid import uuid4

from academic_ingest.adapters.base import AdapterContext
from academic_ingest.adapters.uw.major_detail import MajorDetailAdapter
from academic_ingest.adapters.uw.majors_index import MajorsIndexAdapter
from academic_ingest.classification.page_classifier import PageClassifier
from academic_ingest.models.domain import Program
from academic_ingest.models.enums import MajorType


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


def test_majors_index_preserves_official_types_and_links() -> None:
    result = MajorsIndexAdapter().extract(
        context(
            "majors_index.html",
            "https://admit.washington.edu/academics/majors/",
        )
    )

    programs = {item.official_name: item for item in result.records}
    assert programs["Computer Science"].major_type is MajorType.CAPACITY_CONSTRAINED
    assert programs["Mathematics"].major_type is MajorType.MINIMUM_REQUIREMENTS
    assert "Data Science" not in programs
    assert "https://admit.washington.edu/majors/informatics/" in result.discovered_links


def test_recommended_preparation_is_not_mandatory() -> None:
    result = MajorDetailAdapter().extract(
        context(
            "major_detail.html",
            "https://admit.washington.edu/majors/informatics/",
        )
    )
    preparation = next(
        item for item in result.requirements if item.name == "Competitive preparation"
    )

    assert preparation.recommended is True
    assert preparation.mandatory is False


def test_major_detail_separates_requirements_notes_and_outcomes() -> None:
    result = MajorDetailAdapter().extract(
        context(
            "major_detail.html",
            "https://admit.washington.edu/majors/informatics/",
        )
    )
    program = next(item for item in result.records if isinstance(item, Program))
    required = next(item for item in result.requirements if item.mandatory)

    assert program.official_name == "Informatics"
    assert program.major_type is MajorType.CAPACITY_CONSTRAINED
    assert program.application_required is True
    assert program.application_terms == ["autumn", "spring"]
    assert required.minimum_grade == 2
    assert {"INFO 200", "CSE 121", "CSE 122", "CSE 123", "CSE 143", "STAT 311", "QMETH 201"} <= set(
        required.allowed_courses
    )
    assert "INFO 200 may be completed after transfer" in required.evidence[0].footnote_context
    assert [statistic.label for statistic in result.outcome_statistics] == [
        "Total undergraduates",
        "Total from Washington community colleges",
    ]
    assert all("Total" not in requirement.description for requirement in result.requirements)


def test_conflicting_claims_are_emitted_without_choosing_a_winner() -> None:
    result = MajorDetailAdapter().extract(
        context(
            "major_detail_conflict.html",
            "https://admit.washington.edu/majors/statistics/",
        )
    )

    assert [(claim.source, claim.value) for claim in result.conflict_candidates] == [
        ("admissions", "Minimum grade of 2.0 in STAT 311."),
        ("department", "Department page says minimum grade 2.5 in STAT 311."),
    ]


def test_cards_fallback_does_not_crash_when_no_major_cards() -> None:
    """Regression test for fallback path when no article.major-card or [data-major] elements exist.

    This tests the fallback selector that looks for anchors nested two levels deep.
    Ensures that mem_id property access (not method call) doesn't raise TypeError.
    """
    html = b"""
    <html>
        <body>
            <div class="majors-list">
                <section>
                    <div class="major-item">
                        <div class="major-info">
                            <a href="https://admit.washington.edu/majors/informatics/">Informatics</a>
                            <p>Major type: Capacity-constrained</p>
                        </div>
                    </div>
                </section>
                <section>
                    <div class="major-item">
                        <div class="major-info">
                            <a href="https://admit.washington.edu/majors/computer-science/">
                                Computer Science
                            </a>
                            <p>Major type: Open</p>
                        </div>
                    </div>
                </section>
            </div>
        </body>
    </html>
    """

    adapter_context = AdapterContext(
        page=PageClassifier().classify(
            "https://admit.washington.edu/academics/majors/",
            html,
            content_type="text/html",
        ),
        raw_content=html,
        source_snapshot_id=uuid4(),
        crawl_job_id=uuid4(),
        institution_id="uw-seattle",
        campus="Seattle",
    )

    result = MajorsIndexAdapter().extract(adapter_context)

    # Verify we got programs and didn't crash
    assert len(result.records) >= 1
    program_names = {item.official_name for item in result.records}
    assert "Informatics" in program_names or "Computer Science" in program_names
