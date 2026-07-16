from pathlib import Path
from uuid import uuid4

from academic_ingest.adapters.base import AdapterContext
from academic_ingest.adapters.registry import AdapterRegistry
from academic_ingest.adapters.uw.transfer_admissions import TransferAdmissionsAdapter
from academic_ingest.adapters.uw.transfer_policies import TransferPolicyAdapter
from academic_ingest.classification.page_classifier import PageClassifier


def test_transfer_pages_flow_through_specific_adapters() -> None:
    registry = AdapterRegistry([TransferAdmissionsAdapter(), TransferPolicyAdapter()])
    classifier = PageClassifier()
    record_types: set[str] = set()

    for fixture, url in [
        ("transfer_admissions.html", "https://admit.washington.edu/apply/transfer/"),
        (
            "transfer_policies.html",
            "https://admit.washington.edu/apply/transfer/policies/",
        ),
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
        record_types.update(type(item).__name__ for item in result.records)

    assert record_types == {"AdmissionsRule", "TransferPolicy"}
