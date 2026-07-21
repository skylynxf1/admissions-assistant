from __future__ import annotations

from urllib.parse import urlsplit

from academic_ingest.models.enums import Severity
from academic_ingest.validation.models import ValidationIssue


def _is_allowed_host(url: str, allowed_hosts: set[str]) -> bool:
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme != "https":
        return False
    return any(host == allowed or host.endswith("." + allowed) for allowed in allowed_hosts)


def validate_source_scope(
    url: str,
    campus: str,
    *,
    allowed_hosts: set[str],
    destination_campus: str,
    disallowed_campus_patterns: set[str],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not _is_allowed_host(url, allowed_hosts):
        issues.append(
            ValidationIssue(
                code="source_outside_official_scope",
                message=f"Evidence URL is not on an approved official HTTPS host: {url}",
                severity=Severity.ERROR,
                disposition="block_publish",
                field="source_url",
            )
        )
    campus_folded = campus.casefold()
    out_of_scope = campus_folded != destination_campus.casefold()
    if not out_of_scope:
        out_of_scope = any(
            pattern.casefold() in campus_folded for pattern in disallowed_campus_patterns
        )
    if out_of_scope:
        issues.append(
            ValidationIssue(
                code="campus_out_of_scope",
                message=(
                    f"Only {destination_campus} records may be published; received {campus!r}."
                ),
                severity=Severity.ERROR,
                disposition="block_publish",
                field="campus",
            )
        )
    return issues


def uw_seattle_scope(url: str, campus: str) -> list[ValidationIssue]:
    return validate_source_scope(
        url,
        campus,
        allowed_hosts={"washington.edu", "uw.edu"},
        destination_campus="Seattle",
        disallowed_campus_patterns={"bothell", "tacoma"},
    )
