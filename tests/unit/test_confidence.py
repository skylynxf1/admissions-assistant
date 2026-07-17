from academic_ingest.confidence.rules import ConfidenceFactors
from academic_ingest.confidence.scorer import score_confidence
from academic_ingest.models.enums import ConfidenceTier


def test_fully_supported_deterministic_record_is_publishable() -> None:
    decision = score_confidence(
        ConfidenceFactors(
            official_source=True,
            exact_evidence=True,
            deterministic_parser=True,
            schema_valid=True,
            current_or_dated=True,
            corroborated=True,
        )
    )

    assert decision.publishable is True
    assert decision.tier == ConfidenceTier.VERIFIED
    assert decision.score == 1.0
    assert decision.factor_explanations["exact_evidence"] == "verified in source snapshot"


def test_conflict_is_a_hard_publish_blocker_with_explanation() -> None:
    decision = score_confidence(
        ConfidenceFactors(
            official_source=True,
            exact_evidence=True,
            deterministic_parser=True,
            schema_valid=True,
            current_or_dated=True,
            conflict_count=1,
        )
    )

    assert decision.publishable is False
    assert decision.tier == ConfidenceTier.NEEDS_REVIEW
    assert "unresolved source conflict" in decision.blocking_reasons


def test_unresolved_fields_and_material_change_route_to_review() -> None:
    decision = score_confidence(
        ConfidenceFactors(
            official_source=True,
            exact_evidence=True,
            deterministic_parser=True,
            schema_valid=True,
            unresolved_field_count=2,
            material_change=True,
        )
    )

    assert decision.publishable is False
    assert decision.requires_review is True
    assert decision.factor_explanations["unresolved_fields"] == "2 unresolved field(s)"
    assert decision.factor_explanations["material_change"] == "material source change detected"
