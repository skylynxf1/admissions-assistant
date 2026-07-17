from __future__ import annotations

import hashlib
import json
from collections import defaultdict

import networkx as nx

from app.eligibility import PrerequisiteEligibilityEvaluator
from app.graph import PrerequisiteGraph, build_prerequisite_graph
from app.models import (
    CandidateCourse,
    CompletedCourse,
    Confidence,
    Course,
    CourseEquivalency,
    CourseRecommendation,
    CourseRecommendationFeatures,
    EquivalencyType,
    ExcludedCourse,
    OfferingStatus,
    RecommendationExplanationContext,
    RecommendationRequest,
    RecommendationResponse,
    ScenarioDataset,
    StudentCourseStatus,
)
from app.repository import RecommendationRepository
from app.scoring import (
    WeightedRecommendationScorer,
    deterministic_reasons,
    deterministic_warnings,
    risk_level,
    usefulness_label,
)

ACCEPTED_EQUIVALENCIES = {
    EquivalencyType.DIRECT,
    EquivalencyType.DEPARTMENTAL_ELECTIVE,
    EquivalencyType.GENERAL_ELECTIVE,
}
CONFIDENCE_RANK = {
    Confidence.HIGH: 3,
    Confidence.MEDIUM: 2,
    Confidence.LOW: 1,
    Confidence.UNKNOWN: 0,
}


class RecommendationService:
    def __init__(self, repository: RecommendationRepository) -> None:
        self.repository = repository
        self.scorer = WeightedRecommendationScorer()

    async def recommend(
        self, scenario_id: str, request: RecommendationRequest
    ) -> RecommendationResponse:
        dataset = await self.repository.load_dataset(scenario_id)
        fingerprint = scenario_fingerprint(dataset, request)
        cached = await self.repository.get_cached(scenario_id, request.target_term, fingerprint)
        if cached:
            return cached.model_copy(
                update={"recommendations": cached.recommendations[: request.max_results]}, deep=True
            )

        graph = build_prerequisite_graph(
            dataset.courses, dataset.prerequisite_groups, dataset.offerings
        )
        candidates, excluded = self.generate_candidate_courses(
            dataset, graph, request.target_term, request.include_uncertain
        )
        required_course_ids, requirement_by_course = self._required_courses(dataset)
        recommendations = [
            self._recommendation(
                candidate,
                dataset,
                graph,
                required_course_ids,
                requirement_by_course,
            )
            for candidate in candidates
        ]
        recommendations.sort(key=lambda item: (-item.score, item.course_code, item.course_id))
        for rank, recommendation in enumerate(recommendations, start=1):
            recommendation.rank = rank

        full_response = RecommendationResponse(
            scenario_id=scenario_id,
            target_term=request.target_term,
            recommendations=recommendations,
            excluded_courses=excluded,
            data_warnings=dataset.data_warnings,
            scenario_fingerprint=fingerprint,
        )
        await self.repository.save_cached(
            full_response,
            dataset.weight_config.version_key,
            dataset.academic_data_version,
        )
        return full_response.model_copy(
            update={"recommendations": full_response.recommendations[: request.max_results]},
            deep=True,
        )

    def generate_candidate_courses(
        self,
        dataset: ScenarioDataset,
        graph: PrerequisiteGraph,
        target_term: str,
        include_uncertain: bool,
    ) -> tuple[list[CandidateCourse], list[ExcludedCourse]]:
        completed = [
            CompletedCourse(
                course_id=item.course_id,
                grade_points=item.grade_points,
                credits_earned=float(item.credits_earned or 0),
            )
            for item in dataset.student_courses
            if item.status == StudentCourseStatus.COMPLETED and item.course_id
        ]
        completed_ids = {item.course_id for item in completed}
        in_progress_ids = {
            item.course_id
            for item in dataset.student_courses
            if item.status == StudentCourseStatus.IN_PROGRESS and item.course_id
        }
        evaluator = PrerequisiteEligibilityEvaluator(dataset.prerequisite_groups)
        required_course_ids, _ = self._required_courses(dataset)
        offerings = self._offerings_by_course(dataset)
        candidates: list[CandidateCourse] = []
        excluded: list[ExcludedCourse] = []

        for course in sorted(dataset.courses, key=lambda item: (item.course_code, item.id)):
            reason: str | None = None
            eligibility = evaluator.evaluate_course_eligibility(
                course.id,
                completed,
                in_progress_ids,
                dataset.placement_results,
                dataset.admitted_program_ids,
            )
            if (
                not course.active
                or course.institution_id != dataset.scenario.current_institution_id
            ):
                continue
            if course.id in completed_ids:
                reason = "Course is already completed."
            elif not self._offered_in_term(offerings.get(course.id, []), target_term):
                reason = f"No confirmed or typical offering for {target_term}."
            elif not (eligibility.eligible or eligibility.eligible_with_concurrent_enrollment):
                missing = [
                    self._course_code(dataset, value) for value in eligibility.missing_courses
                ]
                reason = (
                    "Missing prerequisite " + ", ".join(missing) + "."
                    if missing
                    else "Prerequisite conditions are not satisfied."
                )
            elif (
                dataset.scenario.max_credits is not None
                and course.credits > dataset.scenario.max_credits
            ):
                reason = "Course exceeds the scenario maximum credits."
            else:
                relevant = self._is_relevant(course.id, dataset, graph, required_course_ids)
                if not relevant:
                    reason = (
                        "Course does not apply to a selected program, general education, "
                        "or prerequisite chain."
                    )
                elif self._duplicate_credit_risk(course.id, dataset, completed_ids):
                    reason = "Course may duplicate credit already completed."
                else:
                    uncertain = self._is_uncertain(course.id, dataset)
                    if uncertain and not include_uncertain:
                        reason = "Applicability is uncertain and include_uncertain is false."
                    else:
                        candidates.append(
                            CandidateCourse(
                                course=course, eligibility=eligibility, uncertain=uncertain
                            )
                        )
            if reason:
                excluded.append(
                    ExcludedCourse(
                        course_id=course.id, course_code=course.course_code, reason=reason
                    )
                )
        return candidates, excluded

    def _recommendation(
        self,
        candidate: CandidateCourse,
        dataset: ScenarioDataset,
        graph: PrerequisiteGraph,
        required_course_ids: set[str],
        requirement_by_course: dict[str, list[tuple[str, str, int, list[str]]]],
    ) -> CourseRecommendation:
        features = self._features(
            candidate.course,
            dataset,
            graph,
            required_course_ids,
            requirement_by_course,
        )
        priorities = [item.priority for item in dataset.scenario.selected_programs]
        score = self.scorer.score(
            features,
            dataset.weight_config,
            all_program_priorities=priorities,
            selected_institution_count=len(dataset.scenario.selected_institution_ids),
        )
        return CourseRecommendation(
            course_id=candidate.course.id,
            course_code=candidate.course.course_code,
            title=candidate.course.title,
            score=score.score,
            rank=0,
            eligibility=candidate.eligibility,
            features=features,
            score_breakdown=score.breakdown,
            usefulness_label=usefulness_label(features),
            risk_level=risk_level(
                features.dead_end_risk,
                features.duplicate_credit_risk,
                features.equivalency_confidence,
            ),
            reasons=deterministic_reasons(features),
            warnings=deterministic_warnings(
                features, candidate.eligibility.eligible_with_concurrent_enrollment
            ),
            source_ids=features.source_ids,
        )

    def _features(
        self,
        course: Course,
        dataset: ScenarioDataset,
        graph: PrerequisiteGraph,
        required_course_ids: set[str],
        requirement_by_course: dict[str, list[tuple[str, str, int, list[str]]]],
    ) -> CourseRecommendationFeatures:
        helped_programs: set[str] = set()
        priorities: set[int] = set()
        requirements: set[str] = set()
        source_ids: set[str] = set(course.source_ids)
        selected_program_ids = {item.program_id for item in dataset.scenario.selected_programs}

        for required_course_id, entries in requirement_by_course.items():
            applies = course.id == required_course_id or graph.has_path(
                course.id, required_course_id
            )
            matching_equivalencies = [
                item
                for item in dataset.equivalencies
                if item.source_course_id == course.id
                and item.target_course_id == required_course_id
                and item.equivalency_type == EquivalencyType.DIRECT
                and item.confidence != Confidence.UNKNOWN
            ]
            applies = applies or bool(matching_equivalencies)
            if not applies:
                continue
            for program_id, requirement_name, priority, requirement_sources in entries:
                if program_id not in selected_program_ids:
                    continue
                helped_programs.add(program_id)
                priorities.add(priority)
                requirements.add(requirement_name)
                source_ids.update(requirement_sources)
            for equivalency in matching_equivalencies:
                source_ids.update(equivalency.source_ids)

        ge_mappings = [
            item
            for item in dataset.general_education_mappings
            if item.course_id == course.id
            and item.status in {"CONFIRMED", "LIKELY"}
            and item.confidence != Confidence.UNKNOWN
        ]
        ge_categories = sorted({item.category_code for item in ge_mappings})
        for mapping in ge_mappings:
            source_ids.update(mapping.source_ids)

        direct = [item.course_id for item in graph.get_directly_unlocked_courses(course.id)]
        descendants = [item.course_id for item in graph.get_all_unlocked_descendants(course.id)]
        required_descendants = sorted(set(descendants) & required_course_ids)
        coverage = self._university_coverage(course.id, dataset, helped_programs)
        helped_institutions = sorted(key for key, values in coverage.items() if values)
        relevant_equivalencies = [
            item
            for item in dataset.equivalencies
            if item.source_course_id == course.id
            and item.target_institution_id in dataset.scenario.selected_institution_ids
        ]
        for equivalency in relevant_equivalencies:
            source_ids.update(equivalency.source_ids)
        equivalency_confidence = self._best_confidence(relevant_equivalencies)
        infrequent = self._offered_infrequently(
            self._offerings_by_course(dataset).get(course.id, [])
        )
        depth_reduction = max(
            (
                nx.shortest_path_length(graph.graph, course.id, target)
                for target in required_descendants
            ),
            default=0,
        )
        terms_saved = 0
        if required_descendants:
            terms_saved = 1
            if infrequent and depth_reduction >= 3:
                terms_saved = 2
        completed_ids = {
            item.course_id
            for item in dataset.student_courses
            if item.status == StudentCourseStatus.COMPLETED and item.course_id
        }
        duplicate_risk = self._duplicate_credit_risk(course.id, dataset, completed_ids)
        dead_end_risk, dead_end_factors = self._dead_end_risk(
            helped_programs,
            priorities,
            ge_categories,
            required_descendants,
            coverage,
            relevant_equivalencies,
        )
        return CourseRecommendationFeatures(
            course_id=course.id,
            selected_programs_helped=len(helped_programs),
            selected_institutions_helped=len(helped_institutions),
            requirements_satisfied=sorted(requirements),
            general_education_categories_satisfied=ge_categories,
            directly_unlocked_courses=sorted(direct),
            descendant_courses_unlocked=sorted(descendants),
            required_descendants_unlocked=required_descendants,
            dependency_depth_reduction=depth_reduction,
            estimated_graduation_terms_saved=terms_saved,
            offered_infrequently=infrequent,
            equivalency_confidence=equivalency_confidence.value,
            duplicate_credit_risk=duplicate_risk,
            dead_end_risk=dead_end_risk,
            scenario_priorities_helped=sorted(priorities),
            university_coverage=coverage,
            dead_end_factors=dead_end_factors,
            source_ids=sorted(source_ids),
        )

    @staticmethod
    def _required_courses(
        dataset: ScenarioDataset,
    ) -> tuple[set[str], dict[str, list[tuple[str, str, int, list[str]]]]]:
        selected = {item.program_id: item.priority for item in dataset.scenario.selected_programs}
        requirements = {
            item.id: item
            for item in dataset.program_requirements
            if item.program_id in selected and item.required
        }
        mapping: dict[str, list[tuple[str, str, int, list[str]]]] = defaultdict(list)
        for option in dataset.requirement_course_options:
            requirement = requirements.get(option.program_requirement_id)
            if not requirement:
                continue
            mapping[option.course_id].append(
                (
                    requirement.program_id,
                    requirement.name,
                    selected[requirement.program_id],
                    sorted(set(requirement.source_ids + option.source_ids)),
                )
            )
        for equivalency in dataset.equivalencies:
            if (
                equivalency.equivalency_type == EquivalencyType.DIRECT
                and equivalency.confidence != Confidence.UNKNOWN
                and equivalency.target_course_id in mapping
            ):
                mapping[equivalency.source_course_id].extend(mapping[equivalency.target_course_id])
        return set(mapping), mapping

    @staticmethod
    def _offerings_by_course(dataset: ScenarioDataset) -> dict[str, list]:
        values: dict[str, list] = defaultdict(list)
        for offering in dataset.offerings:
            values[offering.course_id].append(offering)
        return values

    @staticmethod
    def _offered_in_term(offerings: list, target_term: str) -> bool:
        target = target_term.lower()
        season = target.split("-")[0]
        return any(
            item.offering_status in {OfferingStatus.CONFIRMED, OfferingStatus.TYPICALLY_OFFERED}
            and (item.term_name.lower() == target or item.term_name.lower().split("-")[0] == season)
            for item in offerings
        )

    @staticmethod
    def _offered_infrequently(offerings: list) -> bool:
        offered_seasons = {
            item.term_name.lower().split("-")[0]
            for item in offerings
            if item.offering_status in {OfferingStatus.CONFIRMED, OfferingStatus.TYPICALLY_OFFERED}
        }
        return (
            bool(offered_seasons)
            and len(offered_seasons & {"autumn", "fall", "winter", "spring"}) < 3
        )

    def _is_relevant(
        self,
        course_id: str,
        dataset: ScenarioDataset,
        graph: PrerequisiteGraph,
        required_course_ids: set[str],
    ) -> bool:
        if course_id in required_course_ids:
            return True
        if any(graph.has_path(course_id, target) for target in required_course_ids):
            return True
        if any(
            item.course_id == course_id and item.status in {"CONFIRMED", "LIKELY"}
            for item in dataset.general_education_mappings
        ):
            return True
        return any(
            item.source_course_id == course_id
            and item.target_course_id in required_course_ids
            and item.equivalency_type == EquivalencyType.DIRECT
            for item in dataset.equivalencies
        )

    @staticmethod
    def _duplicate_credit_risk(
        course_id: str, dataset: ScenarioDataset, completed_ids: set[str]
    ) -> bool:
        if course_id in completed_ids:
            return True
        candidate_targets = {
            item.target_course_id
            for item in dataset.equivalencies
            if item.source_course_id == course_id
            and item.equivalency_type == EquivalencyType.DIRECT
            and item.target_course_id
        }
        completed_targets = set(completed_ids)
        for item in dataset.equivalencies:
            if item.source_course_id in completed_ids and item.target_course_id:
                completed_targets.add(item.target_course_id)
        return bool(candidate_targets & completed_targets)

    @staticmethod
    def _is_uncertain(course_id: str, dataset: ScenarioDataset) -> bool:
        course = next(item for item in dataset.courses if item.id == course_id)
        if course.confidence in {Confidence.LOW, Confidence.UNKNOWN}:
            return True
        related = [item for item in dataset.equivalencies if item.source_course_id == course_id]
        return bool(related) and all(
            item.confidence in {Confidence.LOW, Confidence.UNKNOWN}
            or item.equivalency_type in {EquivalencyType.REQUIRES_REVIEW, EquivalencyType.UNKNOWN}
            for item in related
        )

    @staticmethod
    def _best_confidence(equivalencies: list[CourseEquivalency]) -> Confidence:
        accepted = [
            item.confidence
            for item in equivalencies
            if item.equivalency_type in ACCEPTED_EQUIVALENCIES
        ]
        return (
            max(accepted, key=lambda value: CONFIDENCE_RANK[value])
            if accepted
            else Confidence.UNKNOWN
        )

    @staticmethod
    def _university_coverage(
        course_id: str,
        dataset: ScenarioDataset,
        helped_programs: set[str],
    ) -> dict[str, list[str]]:
        outcomes: dict[str, set[str]] = {
            institution_id: set() for institution_id in dataset.scenario.selected_institution_ids
        }
        program_institutions = {
            item.institution_id for item in dataset.programs if item.id in helped_programs
        }
        for institution_id in program_institutions:
            outcomes.setdefault(institution_id, set()).add("PREREQUISITE_APPLICABLE")
        for mapping in dataset.general_education_mappings:
            if (
                mapping.course_id == course_id
                and mapping.institution_id in outcomes
                and mapping.status in {"CONFIRMED", "LIKELY"}
                and mapping.confidence != Confidence.UNKNOWN
            ):
                outcomes[mapping.institution_id].add("GENERAL_EDUCATION")
        for equivalency in dataset.equivalencies:
            if (
                equivalency.source_course_id != course_id
                or equivalency.target_institution_id not in outcomes
            ):
                continue
            if (
                equivalency.equivalency_type == EquivalencyType.DIRECT
                and equivalency.confidence != Confidence.UNKNOWN
            ):
                outcomes[equivalency.target_institution_id].add("DIRECT_EQUIVALENT")
            elif (
                equivalency.equivalency_type == EquivalencyType.DEPARTMENTAL_ELECTIVE
                and equivalency.confidence != Confidence.UNKNOWN
            ):
                outcomes[equivalency.target_institution_id].add("DEPARTMENTAL_ELECTIVE")
            elif (
                equivalency.equivalency_type == EquivalencyType.GENERAL_ELECTIVE
                and equivalency.confidence != Confidence.UNKNOWN
            ):
                outcomes[equivalency.target_institution_id].add("TRANSFERABLE_ELECTIVE")
        return {key: sorted(values) for key, values in sorted(outcomes.items())}

    @staticmethod
    def _dead_end_risk(
        helped_programs: set[str],
        priorities: set[int],
        ge_categories: list[str],
        required_descendants: list[str],
        coverage: dict[str, list[str]],
        equivalencies: list[CourseEquivalency],
    ) -> tuple[float, list[str]]:
        risk = 0.6
        factors: list[str] = []
        if len(helped_programs) >= 2:
            risk -= 0.25
            factors.append("applies to multiple selected programs")
        elif len(helped_programs) == 1:
            risk -= 0.1
            factors.append("applies to one selected program")
        else:
            factors.append("does not directly satisfy a selected program requirement")
        if priorities and min(priorities) >= 3 and len(helped_programs) == 1:
            risk += 0.1
            factors.append("helps only a lower-priority program")
        if ge_categories:
            risk -= 0.15
            factors.append("also satisfies general education")
        else:
            factors.append("no general-education mapping")
        if required_descendants:
            risk -= 0.2
            factors.append("unlocks required descendants")
        else:
            factors.append("unlocks no required descendant")
        accepted_institutions = sum(bool(values) for values in coverage.values())
        if accepted_institutions >= 2:
            risk -= 0.15
            factors.append("accepted across multiple selected institutions")
        elif accepted_institutions == 0:
            risk += 0.15
            factors.append("no accepted applicability at selected institutions")
        direct_count = sum(
            item.equivalency_type == EquivalencyType.DIRECT
            and item.confidence in {Confidence.HIGH, Confidence.MEDIUM}
            for item in equivalencies
        )
        if direct_count:
            risk -= 0.1
            factors.append("has a direct equivalency")
        elif equivalencies and all(
            item.equivalency_type == EquivalencyType.GENERAL_ELECTIVE for item in equivalencies
        ):
            risk += 0.1
            factors.append("transfers only as general elective credit")
        if equivalencies and all(
            item.confidence in {Confidence.LOW, Confidence.UNKNOWN} for item in equivalencies
        ):
            risk += 0.2
            factors.append("applicability evidence is uncertain")
        return round(max(0.0, min(1.0, risk)), 3), factors

    @staticmethod
    def _course_code(dataset: ScenarioDataset, course_id: str) -> str:
        return next(
            (item.course_code for item in dataset.courses if item.id == course_id), course_id
        )

    @staticmethod
    def explanation_context(
        recommendation: CourseRecommendation,
        dataset: ScenarioDataset,
        verified_source_summaries: list[str],
    ) -> RecommendationExplanationContext:
        selected_ids = {item.program_id for item in dataset.scenario.selected_programs}
        return RecommendationExplanationContext(
            student_goal_summary=dataset.scenario.name or "Multi-program academic plan",
            recommendation=recommendation,
            selected_program_names=sorted(
                item.name for item in dataset.programs if item.id in selected_ids
            ),
            selected_institution_names=dataset.scenario.selected_institution_ids,
            verified_source_summaries=verified_source_summaries,
        )


def scenario_fingerprint(dataset: ScenarioDataset, request: RecommendationRequest) -> str:
    student_courses = sorted(
        [
            {
                "course_id": item.course_id,
                "raw": item.course_code_raw,
                "status": item.status.value,
                "grade_points": item.grade_points,
                "credits": item.credits_earned,
            }
            for item in dataset.student_courses
        ],
        key=lambda item: (item["course_id"] or "", item["raw"], item["status"]),
    )
    value = {
        "student_courses": student_courses,
        "programs": sorted(
            [(item.program_id, item.priority) for item in dataset.scenario.selected_programs]
        ),
        "institutions": sorted(dataset.scenario.selected_institution_ids),
        "target_term": request.target_term,
        "residency": dataset.scenario.residency_status,
        "institution_type": dataset.scenario.institution_type,
        "max_credits": dataset.scenario.max_credits,
        "graduation_target": dataset.scenario.graduation_target,
        "weight_version": dataset.weight_config.version_key,
        "academic_data_version": dataset.academic_data_version,
        "include_uncertain": request.include_uncertain,
    }
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


async def generate_candidate_courses(
    scenario_id: str,
    target_term: str,
    repository: RecommendationRepository,
    *,
    include_uncertain: bool = False,
) -> list[CandidateCourse]:
    dataset = await repository.load_dataset(scenario_id)
    graph = build_prerequisite_graph(
        dataset.courses, dataset.prerequisite_groups, dataset.offerings
    )
    candidates, _ = RecommendationService(repository).generate_candidate_courses(
        dataset, graph, target_term, include_uncertain
    )
    return candidates
