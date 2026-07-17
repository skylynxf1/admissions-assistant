from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from uuid import UUID

from academic_ingest.fetching.client import FetchOutcome, FetchResult, SafeFetchClient
from academic_ingest.models.domain import PipelineIssue, SkippedItem
from academic_ingest.models.enums import Severity


@dataclass
class CrawlAcquisitionResult:
    fetched: list[FetchResult] = field(default_factory=list)
    skipped: list[SkippedItem] = field(default_factory=list)
    errors: list[PipelineIssue] = field(default_factory=list)


async def run_crawl_job(
    urls: Sequence[str],
    *,
    crawl_job_id: UUID,
    fetch_client: SafeFetchClient,
) -> CrawlAcquisitionResult:
    result = CrawlAcquisitionResult()
    for url in urls:
        try:
            fetched = await fetch_client.fetch(url, crawl_job_id)
        except Exception as error:
            result.errors.append(
                PipelineIssue(
                    code="page_fetch_failed",
                    message=f"{type(error).__name__}: {error}",
                    source_url=url,
                    severity=Severity.ERROR,
                )
            )
            continue
        if fetched.outcome == FetchOutcome.FETCHED:
            result.fetched.append(fetched)
        elif fetched.outcome in {FetchOutcome.SKIPPED, FetchOutcome.NOT_MODIFIED}:
            result.skipped.append(
                SkippedItem(
                    source_url=url,
                    reason=fetched.skip_reason or fetched.outcome.value,
                )
            )
        else:
            result.errors.append(
                PipelineIssue(
                    code="page_fetch_failed",
                    message=fetched.skip_reason or "fetch failed",
                    source_url=url,
                    severity=Severity.ERROR,
                )
            )
    return result

