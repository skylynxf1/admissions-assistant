from __future__ import annotations

from urllib.parse import urlsplit

from academic_ingest.models.enums import Severity
from academic_ingest.validation.models import ValidationIssue


def is_official_uw_url(url: str) -> bool:
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower().rstrip(".")
    return parsed.scheme == "https" and (
        host == "washington.edu" or host.endswith(".washington.edu") or host == "uw.edu"
    )


def validate_source_scope(url: str, campus: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not is_official_uw_url(url):
        issues.append(
            ValidationIssue(
                code="source_outside_official_scope",
                message=f"Evidence URL is not on an approved official UW HTTPS host: {url}",
                severity=Severity.ERROR,
                disposition="block_publish",
                field="source_url",
            )
        )
    if campus.casefold() != "seattle":
        issues.append(
            ValidationIssue(
                code="campus_out_of_scope",
                message=f"Only UW Seattle records may be published; received {campus!r}.",
                severity=Severity.ERROR,
                disposition="block_publish",
                field="campus",
            )
        )
    return issues
