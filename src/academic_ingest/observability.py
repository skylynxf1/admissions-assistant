from __future__ import annotations

from collections import Counter
from typing import Any
from uuid import UUID

import structlog

from academic_ingest.models.domain import PipelineResult


class PipelineTelemetry:
    """Small in-process counters suitable for logs or a metrics adapter."""

    def __init__(self) -> None:
        self._counts: Counter[str] = Counter()

    def increment(self, name: str, value: int = 1) -> None:
        if value < 0:
            raise ValueError("counter increments cannot be negative")
        self._counts[name] += value

    def snapshot(self) -> dict[str, int]:
        return dict(sorted(self._counts.items()))


def pipeline_summary_fields(result: PipelineResult, crawl_job_id: UUID | str) -> dict[str, Any]:
    return {
        "crawl_job_id": str(crawl_job_id),
        "pages_attempted": result.parser_metrics.pages_attempted,
        "parse_successes": result.parser_metrics.parse_successes,
        "parse_failures": result.parser_metrics.parse_failures,
        "records_extracted": result.parser_metrics.records_extracted,
        "gpt_fallback_calls": result.parser_metrics.gpt_fallback_calls,
        "warning_codes": [warning.code for warning in result.warnings],
        "error_codes": [error.code for error in result.errors],
        "review_task_count": len(result.review_tasks),
    }


def log_pipeline_summary(result: PipelineResult, crawl_job_id: UUID | str) -> None:
    structlog.get_logger("academic_ingest.pipeline").info(
        "pipeline_completed",
        **pipeline_summary_fields(result, crawl_job_id),
    )
