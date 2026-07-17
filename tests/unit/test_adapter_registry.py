from pathlib import Path
from uuid import uuid4

import pytest

from academic_ingest.adapters.base import AdapterContext
from academic_ingest.adapters.registry import AdapterRegistry
from academic_ingest.adapters.uw.course_catalog import CourseCatalogAdapter
from academic_ingest.classification.page_classifier import PageClassifier


def test_classifier_and_registry_select_course_catalog_adapter() -> None:
    html = Path("tests/fixtures/uw/html/courses_cse.html").read_bytes()
    page = PageClassifier().classify(
        "https://www.washington.edu/students/crscat/cse.html",
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
    registry = AdapterRegistry([CourseCatalogAdapter()])

    assert page.adapter_name == "uw.course_catalog"
    assert registry.for_context(context).name == "uw.course_catalog"


def test_registry_rejects_duplicate_adapter_names() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        AdapterRegistry([CourseCatalogAdapter(), CourseCatalogAdapter()])
