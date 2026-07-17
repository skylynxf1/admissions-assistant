from datetime import UTC, datetime
from decimal import Decimal

from academic_ingest.conflicts.detector import detect_conflicts
from academic_ingest.models.domain import TransferPolicy
from academic_ingest.models.enums import AuthorityTier


def _policy(
    limit: str,
    *,
    effective_from: datetime | None = None,
    effective_to: datetime | None = None,
) -> TransferPolicy:
    return TransferPolicy(
        institution_id="uw-seattle",
        policy_type="lower_division_limit",
        sending_institution_type="community_college",
        credit_limit=Decimal(limit),
        effective_from=effective_from,
        effective_to=effective_to,
        authority_tier=AuthorityTier.OFFICIAL_REGISTRAR,
    )


def test_overlapping_policy_claims_are_compared_field_by_field() -> None:
    conflicts = detect_conflicts([_policy("90"), _policy("105")])

    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == "overlapping_claims"
    assert conflicts[0].differing_fields == {"credit_limit": [Decimal("90"), Decimal("105")]}
    assert len(conflicts[0].effective_periods) == 2


def test_non_overlapping_effective_periods_are_versions_not_conflicts() -> None:
    conflicts = detect_conflicts(
        [
            _policy(
                "90",
                effective_from=datetime(2024, 1, 1, tzinfo=UTC),
                effective_to=datetime(2024, 12, 31, tzinfo=UTC),
            ),
            _policy(
                "105",
                effective_from=datetime(2025, 1, 1, tzinfo=UTC),
            ),
        ]
    )

    assert conflicts == []


def test_identical_overlapping_claims_are_not_conflicts() -> None:
    assert detect_conflicts([_policy("90"), _policy("90")]) == []
