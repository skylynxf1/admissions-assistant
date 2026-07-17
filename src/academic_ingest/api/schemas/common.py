from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CrawlJobCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    urls: list[str] = Field(default_factory=list, max_length=50)
    allow_network: bool = False


class ReviewResolutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["accepted", "rejected", "resolved"]
    reviewer: str = Field(min_length=1, max_length=255)
    rationale: str = Field(min_length=1, max_length=10_000)


class PageIngestResponse(BaseModel):
    source_page_id: str
    source_snapshot_id: str
    crawl_job_id: str
    records_extracted: int
    records_published: int
    record_version_ids: list[str] = Field(default_factory=list)
    review_task_ids: list[str] = Field(default_factory=list)
    warnings: list[dict[str, object]] = Field(default_factory=list)
    errors: list[dict[str, object]] = Field(default_factory=list)

