from __future__ import annotations

from decimal import Decimal

from academic_ingest.normalization.identifiers import normalize_whitespace


def normalize_credit_range(
    minimum: Decimal, maximum: Decimal | None = None
) -> tuple[Decimal, Decimal]:
    resolved_maximum = minimum if maximum is None else maximum
    if minimum < 0 or resolved_maximum < minimum:
        raise ValueError("invalid credit range")
    return minimum, resolved_maximum


def normalize_designators(values: list[str]) -> list[str]:
    return list(
        dict.fromkeys(normalize_whitespace(value).upper() for value in values if value.strip())
    )
