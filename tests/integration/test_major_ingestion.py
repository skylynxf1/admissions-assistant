from pathlib import Path
from uuid import uuid4

from academic_ingest.adapters.base import AdapterContext
from academic_ingest.adapters.registry import AdapterRegistry
from academic_ingest.adapters.uw.major_detail import MajorDetailAdapter
from academic_ingest.adapters.uw.majors_index import MajorsIndexAdapter
from academic_ingest.classification.page_classifier import PageClassifier


def test_major_index_and_detail_flow_through_registry() -> None:
    registry = AdapterRegistry([MajorsIndexAdapter(), MajorDetailAdapter()])
    classifier = PageClassifier()
    extracted_names: list[str] = []

    for fixture, url in [
        ("majors_index.html", "https://admit.washington.edu/academics/majors/"),
        ("major_detail.html", "https://admit.washington.edu/majors/informatics/"),
    ]:
        html = Path(f"tests/fixtures/uw/html/{fixture}").read_bytes()
        context = AdapterContext(
            page=classifier.classify(url, html, content_type="text/html"),
            raw_content=html,
            source_snapshot_id=uuid4(),
            crawl_job_id=uuid4(),
            institution_id="uw-seattle",
            campus="Seattle",
        )
        result = registry.for_context(context).extract(context)
        extracted_names.extend(
            item.official_name for item in result.records if hasattr(item, "official_name")
        )

    assert extracted_names.count("Informatics") == 2
    assert "Computer Science" in extracted_names
