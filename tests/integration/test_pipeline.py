from uuid import uuid4

from academic_ingest.adapters.base import AdapterContext, AdapterResult
from academic_ingest.adapters.registry import AdapterRegistry
from academic_ingest.classification.page_classifier import ClassifiedPage
from academic_ingest.extraction.fake_client import FakeStructuredExtractionClient
from academic_ingest.extraction.schemas.policy import ExtractionProposal
from academic_ingest.jobs.ingest_job import run_ingest_job
from academic_ingest.models.domain import Course
from academic_ingest.models.enums import PolicyFamily, SourceType


class _PageIsolatedAdapter:
    name = "test_adapter"
    version = "1"

    def matches(self, page: ClassifiedPage) -> bool:
        return page.adapter_name == self.name

    def extract(self, context: AdapterContext) -> AdapterResult:
        if "bad" in context.page.url:
            raise ValueError("synthetic malformed page")
        return AdapterResult(
            records=[
                Course(
                    institution_id="uw-seattle",
                    subject="CSE",
                    number="123",
                    title="Programming III",
                    credits_min=4,
                    credits_max=4,
                )
            ]
        )


def _context(name: str, *, adapter_name: str = "test_adapter") -> AdapterContext:
    page = ClassifiedPage(
        url=f"https://www.washington.edu/{name}",
        title=name,
        content_type="text/html",
        source_type=SourceType.GENERIC_HTML,
        policy_family=PolicyFamily.COURSE,
        adapter_name=adapter_name,
    )
    return AdapterContext(
        page=page,
        raw_content=b"<p>CSE 123 Programming III</p>",
        source_snapshot_id=uuid4(),
        crawl_job_id=uuid4(),
        institution_id="uw-seattle",
        campus="Seattle",
    )


async def test_pipeline_continues_after_one_page_fails() -> None:
    result = await run_ingest_job(
        [_context("bad"), _context("good")],
        extraction_client=FakeStructuredExtractionClient(),
        adapter_registry=AdapterRegistry([_PageIsolatedAdapter()]),
    )

    assert len(result.errors) == 1
    assert len(result.records) == 1
    assert result.parser_metrics.pages_attempted == 2
    assert result.parser_metrics.parse_successes == 1
    assert result.parser_metrics.parse_failures == 1


async def test_pipeline_uses_structured_fallback_only_without_adapter() -> None:
    proposal = ExtractionProposal(
        proposed_fields={"policy_type": "example"},
        exact_evidence_strings=["CSE 123"],
    )
    fake = FakeStructuredExtractionClient(results={"extract_policy": proposal})

    result = await run_ingest_job(
        [_context("fallback", adapter_name="missing")],
        extraction_client=fake,
        adapter_registry=AdapterRegistry(),
    )

    assert result.records == [proposal]
    assert result.parser_metrics.gpt_fallback_calls == 1
    assert result.parser_metrics.parse_successes == 1


async def test_rejected_fallback_becomes_reviewable_error() -> None:
    proposal = ExtractionProposal(
        proposed_fields={"policy_type": "invented"},
        exact_evidence_strings=["not in the source"],
    )
    fake = FakeStructuredExtractionClient(results={"extract_policy": proposal})

    result = await run_ingest_job(
        [_context("fallback", adapter_name="missing")],
        extraction_client=fake,
        adapter_registry=AdapterRegistry(),
    )

    assert result.records == []
    assert result.errors[0].code == "structured_fallback_rejected"
    assert result.parser_metrics.parse_failures == 1

