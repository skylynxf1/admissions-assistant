from __future__ import annotations

from academic_ingest.confidence.rules import ConfidenceDecision, ConfidenceFactors
from academic_ingest.models.enums import ConfidenceTier


def score_confidence(factors: ConfidenceFactors) -> ConfidenceDecision:
    positive_weights = {
        "official_source": 0.20,
        "exact_evidence": 0.25,
        "deterministic_parser": 0.15,
        "schema_valid": 0.20,
        "current_or_dated": 0.10,
        "corroborated": 0.10,
    }
    score = sum(weight for name, weight in positive_weights.items() if getattr(factors, name))
    score -= 0.15 if factors.ambiguous else 0
    score -= min(0.30, factors.unresolved_field_count * 0.10)
    score -= min(0.50, factors.conflict_count * 0.50)
    score -= 0.10 if factors.material_change else 0
    score = round(max(0.0, min(1.0, score)), 2)

    explanations = {
        "official_source": (
            "official UW source" if factors.official_source else "source is outside official scope"
        ),
        "exact_evidence": (
            "verified in source snapshot" if factors.exact_evidence else "exact quote not verified"
        ),
        "deterministic_parser": (
            "deterministic parser" if factors.deterministic_parser else "model-assisted extraction"
        ),
        "schema_valid": "schema valid" if factors.schema_valid else "schema or logic invalid",
        "current_or_dated": (
            "effective date or catalog year present"
            if factors.current_or_dated
            else "effective date is unclear"
        ),
        "corroborated": (
            "corroborated by multiple evidence records"
            if factors.corroborated
            else "single-source evidence"
        ),
        "ambiguous": "ambiguous source language" if factors.ambiguous else "no ambiguity flagged",
        "unresolved_fields": f"{factors.unresolved_field_count} unresolved field(s)",
        "conflicts": f"{factors.conflict_count} unresolved conflict(s)",
        "material_change": (
            "material source change detected"
            if factors.material_change
            else "no material change flagged"
        ),
    }
    blockers: list[str] = []
    if not factors.official_source:
        blockers.append("source is not in official scope")
    if not factors.exact_evidence:
        blockers.append("exact evidence is missing or unverifiable")
    if not factors.schema_valid:
        blockers.append("schema or logical validation failed")
    if factors.ambiguous:
        blockers.append("source interpretation is ambiguous")
    if factors.unresolved_field_count:
        blockers.append("record has unresolved fields")
    if factors.conflict_count:
        blockers.append("unresolved source conflict")
    if factors.material_change:
        blockers.append("material change requires review")

    publishable = not blockers and score >= 0.75
    requires_review = not publishable
    if publishable and score >= 0.90:
        tier = ConfidenceTier.VERIFIED
    elif publishable:
        tier = ConfidenceTier.HIGH_CONFIDENCE
    elif factors.exact_evidence:
        tier = ConfidenceTier.NEEDS_REVIEW
    else:
        tier = ConfidenceTier.UNRESOLVED
    return ConfidenceDecision(
        score=score,
        tier=tier,
        publishable=publishable,
        requires_review=requires_review,
        factor_explanations=explanations,
        blocking_reasons=blockers,
    )
