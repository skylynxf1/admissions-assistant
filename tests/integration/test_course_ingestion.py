from pathlib import Path
from uuid import uuid4

from academic_ingest.adapters.base import AdapterContext
from academic_ingest.adapters.registry import AdapterRegistry
from academic_ingest.adapters.uw.course_catalog import CourseCatalogAdapter
from academic_ingest.classification.page_classifier import PageClassifier


def test_fixture_course_pages_flow_through_classification_and_registry() -> None:
    registry = AdapterRegistry([CourseCatalogAdapter()])
    classifier = PageClassifier()
    codes: set[str] = set()

    for fixture, subject in [("courses_cse.html", "cse"), ("courses_info.html", "info")]:
        html = Path(f"tests/fixtures/uw/html/{fixture}").read_bytes()
        page = classifier.classify(
            f"https://www.washington.edu/students/crscat/{subject}.html",
            html,
            content_type="text/html",
        )
        context = AdapterContext(
            page=page,
            raw_content=html,
            source_snapshot_id=uuid4(),
            crawl_job_id=uuid4(),
            institution_id="uw-seattle",
            campus="Seattle",
        )
        result = registry.for_context(context).extract(context)
        codes.update(item.canonical_code for item in result.records)

    assert {"CSE 143", "CSE 4XX", "INFO 180", "INFO 200"} <= codes
    assert "CSE 399" not in codes
