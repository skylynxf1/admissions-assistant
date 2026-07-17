from __future__ import annotations

import math
from dataclasses import dataclass

from app.models import CourseRecommendationFeatures, RecommendationWeightConfig


@dataclass(frozen=True)
class ScoreResult:
    score: float
    breakdown: dict[str, float]


class WeightedRecommendationScorer:
    """Configurable deterministic scorer; no language model participates here."""

    def score(
        self,
        features: CourseRecommendationFeatures,
        config: RecommendationWeightConfig,
        *,
        all_program_priorities: list[int],
        selected_institution_count: int,
    ) -> ScoreResult:
        total_priority_value = sum(1 / priority for priority in all_program_priorities) or 1
        helped_priority_value = sum(1 / priority for priority in set(features.scenario_priorities_helped))
        major_signal = min(1.0, helped_priority_value / total_priority_value)
        university_signal = min(
            1.0,
            features.selected_institutions_helped / max(1, selected_institution_count),
        )
        unlock_value = (
            len(features.directly_unlocked_courses) * 3
            + math.sqrt(len(features.required_descendants_unlocked)) * 5
        )
        unlock_signal = min(1.0, unlock_value / 15)
        distinct_axes = sum(
            [
                bool(features.requirements_satisfied),
                bool(features.general_education_categories_satisfied),
                features.selected_programs_helped > 1,
                features.selected_institutions_helped > 1,
            ]
        )
        dual_signal = min(1.0, max(0, distinct_axes - 1) / 2)
        acceleration_signal = min(1.0, features.estimated_graduation_terms_saved / 2)
        uncertain_signal = {
            "high": 0.0,
            "medium": 0.5,
            "low": 1.0,
            "unknown": 1.0,
        }.get(features.equivalency_confidence, 1.0)

        raw = {
            "major_coverage_score": config.major_coverage_weight * major_signal,
            "university_coverage_score": config.university_coverage_weight * university_signal,
            "unlock_score": config.unlock_weight * unlock_signal,
            "dual_requirement_score": config.dual_requirement_weight * dual_signal,
            "graduation_acceleration_score": config.graduation_acceleration_weight * acceleration_signal,
            "infrequent_offering_score": config.infrequent_offering_weight * float(features.offered_infrequently),
            "uncertain_equivalency_penalty": -config.uncertain_equivalency_penalty * uncertain_signal,
            "dead_end_penalty": -config.dead_end_penalty * features.dead_end_risk,
            "duplicate_credit_penalty": -config.duplicate_credit_penalty * float(features.duplicate_credit_risk),
        }
        positive_capacity = sum(
            [
                config.major_coverage_weight,
                config.university_coverage_weight,
                config.unlock_weight,
                config.dual_requirement_weight,
                config.graduation_acceleration_weight,
                config.infrequent_offering_weight,
            ]
        ) or 1
        scale = 100 / positive_capacity
        breakdown = {key: round(value * scale, 3) for key, value in raw.items()}
        score = round(max(0.0, min(100.0, sum(breakdown.values()))), 2)
        return ScoreResult(score=score, breakdown=breakdown)


def usefulness_label(features: CourseRecommendationFeatures) -> str:
    if features.equivalency_confidence in {"low", "unknown"} and features.selected_institutions_helped == 0:
        return "UNCLEAR_TRANSFER_VALUE"
    if features.dead_end_risk >= 0.65:
        return "LOW_PORTABILITY"
    if features.selected_programs_helped >= 2 or features.selected_institutions_helped >= 2:
        return "MULTI_PLAN_USEFUL"
    if features.general_education_categories_satisfied and features.required_descendants_unlocked:
        return "BROADLY_USEFUL"
    return "PROGRAM_SPECIFIC"


def risk_level(dead_end_risk: float, duplicate_credit_risk: bool, equivalency_confidence: str) -> str:
    if duplicate_credit_risk or dead_end_risk >= 0.67 or equivalency_confidence in {"low", "unknown"}:
        return "HIGH"
    if dead_end_risk >= 0.34 or equivalency_confidence == "medium":
        return "MEDIUM"
    return "LOW"


def deterministic_reasons(features: CourseRecommendationFeatures) -> list[str]:
    reasons: list[str] = []
    if features.selected_programs_helped:
        reasons.append(
            f"Applies to {features.selected_programs_helped} selected program"
            f"{'s' if features.selected_programs_helped != 1 else ''}."
        )
    if features.selected_institutions_helped:
        reasons.append(
            f"Has accepted applicability records at {features.selected_institutions_helped} selected institution"
            f"{'s' if features.selected_institutions_helped != 1 else ''}."
        )
    if features.general_education_categories_satisfied:
        reasons.append(
            "Satisfies general-education categories: "
            + ", ".join(features.general_education_categories_satisfied)
            + "."
        )
    if features.directly_unlocked_courses or features.descendant_courses_unlocked:
        reasons.append(
            f"Unlocks {len(features.directly_unlocked_courses)} direct and "
            f"{len(features.descendant_courses_unlocked)} downstream course options."
        )
    if features.estimated_graduation_terms_saved:
        reasons.append(
            f"Taking it now may conservatively avoid up to {features.estimated_graduation_terms_saved} term"
            f"{'s' if features.estimated_graduation_terms_saved != 1 else ''} of prerequisite delay."
        )
    if features.offered_infrequently:
        reasons.append("The course is not offered every standard term, increasing the value of taking it now.")
    return reasons or ["Keeps at least one selected academic path open."]


def deterministic_warnings(features: CourseRecommendationFeatures, concurrent: bool) -> list[str]:
    warnings: list[str] = []
    if concurrent:
        warnings.append("Eligibility depends on explicitly permitted concurrent enrollment.")
    if features.equivalency_confidence != "high":
        warnings.append(f"Transfer applicability confidence is {features.equivalency_confidence}; verify the cited source records.")
    if features.duplicate_credit_risk:
        warnings.append("This course may duplicate credit already completed; it is retained only for transparent scoring.")
    if features.dead_end_risk >= 0.65:
        warnings.append("This option has limited portability across the currently selected plans.")
    return warnings
