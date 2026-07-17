from __future__ import annotations

import re

from selectolax.parser import HTMLParser, Node

from academic_ingest.models.domain import EvidenceRecord
from academic_ingest.models.enums import Severity
from academic_ingest.validation.models import ValidationIssue


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _node_with_id(nodes: list[Node], identifier: str) -> Node | None:
    return next((node for node in nodes if node.attributes.get("id") == identifier), None)


def structured_table_evidence_matches(evidence: EvidenceRecord, snapshot: bytes) -> bool:
    """Verify an assembled table citation against its exact DOM table and row."""

    if evidence.table_identifier is None or evidence.row_identifier is None:
        return False
    tree = HTMLParser(snapshot)
    table = _node_with_id(tree.css("table"), evidence.table_identifier)
    if table is None:
        return False
    row = _node_with_id(table.css("tr"), evidence.row_identifier)
    if row is None:
        return False

    snapshot_text = _normalize(tree.root.text(separator=" ", strip=True)) if tree.root else ""
    table_text = _normalize(table.text(separator=" ", strip=True))
    row_text = _normalize(row.text(separator=" ", strip=True))
    assembled_text = _normalize(evidence.evidence_text.replace("|", " "))
    if not row_text or row_text not in assembled_text:
        return False
    if evidence.heading_context and _normalize(evidence.heading_context) not in snapshot_text:
        return False
    if evidence.footnote_context and _normalize(evidence.footnote_context) not in snapshot_text:
        return False

    lines = [line for line in evidence.evidence_text.splitlines() if _normalize(line)]
    if (
        evidence.heading_context
        and lines
        and _normalize(lines[0]) == _normalize(evidence.heading_context)
    ):
        lines = lines[1:]
    fragments = [
        _normalize(fragment)
        for line in lines
        for fragment in line.split("|")
        if _normalize(fragment)
    ]
    return all(fragment in table_text for fragment in fragments)


def validate_table_evidence(evidence: EvidenceRecord) -> list[ValidationIssue]:
    if evidence.table_identifier is None:
        return []
    missing = [
        name
        for name, value in (
            ("heading_context", evidence.heading_context),
            ("row_identifier", evidence.row_identifier),
        )
        if not value
    ]
    if not missing:
        return []
    return [
        ValidationIssue(
            code="incomplete_table_context",
            message="Table evidence is missing: " + ", ".join(missing),
            severity=Severity.WARNING,
            disposition="review",
            evidence_id=evidence.id,
        )
    ]
