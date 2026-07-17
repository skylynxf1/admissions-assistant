from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class GroupType(StrEnum):
    ALL = "ALL"
    ANY = "ANY"
    MIN_COUNT = "MIN_COUNT"


class ConditionType(StrEnum):
    COURSE = "COURSE"
    PLACEMENT = "PLACEMENT"
    CREDIT_COUNT = "CREDIT_COUNT"
    INSTRUCTOR_PERMISSION = "INSTRUCTOR_PERMISSION"
    PROGRAM_ADMISSION = "PROGRAM_ADMISSION"
    OTHER = "OTHER"


class OfferingStatus(StrEnum):
    CONFIRMED = "CONFIRMED"
    TYPICALLY_OFFERED = "TYPICALLY_OFFERED"
    NOT_OFFERED = "NOT_OFFERED"
    UNKNOWN = "UNKNOWN"


class EquivalencyType(StrEnum):
    DIRECT = "DIRECT"
    DEPARTMENTAL_ELECTIVE = "DEPARTMENTAL_ELECTIVE"
    GENERAL_ELECTIVE = "GENERAL_ELECTIVE"
    NO_CREDIT = "NO_CREDIT"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    UNKNOWN = "UNKNOWN"


class StudentCourseStatus(StrEnum):
    COMPLETED = "COMPLETED"
    IN_PROGRESS = "IN_PROGRESS"
    PLANNED = "PLANNED"


class RequirementType(StrEnum):
    SPECIFIC_COURSE = "SPECIFIC_COURSE"
    COURSE_GROUP = "COURSE_GROUP"
    GENERAL_EDUCATION = "GENERAL_EDUCATION"
    ELECTIVE = "ELECTIVE"
    GPA = "GPA"
    ADMISSION = "ADMISSION"
    OTHER = "OTHER"


class Course(FrozenModel):
    id: str
    institution_id: str
    course_code: str
    subject_code: str | None = None
    course_number: str | None = None
    title: str
    description: str | None = None
    credits_min: float | None = None
    credits_max: float | None = None
    credit_system: str | None = None
    active: bool = True
    confidence: Confidence = Confidence.MEDIUM
    source_ids: list[str] = Field(default_factory=list)

    @property
    def credits(self) -> float:
        return float(self.credits_min or self.credits_max or 0)


class CourseOffering(FrozenModel):
    id: str
    course_id: str
    academic_year: int | None = None
    term_name: str
    offering_status: OfferingStatus
    campus: str | None = None
    delivery_mode: str | None = None
    source_ids: list[str] = Field(default_factory=list)


class PrerequisiteCondition(FrozenModel):
    id: str
    prerequisite_group_id: str
    condition_type: ConditionType
    prerequisite_course_id: str | None = None
    admitted_program_id: str | None = None
    minimum_grade: str | None = None
    minimum_grade_points: float | None = None
    may_be_concurrent: bool = False
    placement_test_code: str | None = None
    minimum_placement_score: float | None = None
    minimum_credits: float | None = None
    permission_required: bool = False
    raw_requirement_text: str | None = None
    confidence: Confidence = Confidence.MEDIUM
    source_ids: list[str] = Field(default_factory=list)


class PrerequisiteGroup(FrozenModel):
    id: str
    target_course_id: str
    group_type: GroupType
    group_order: int = 0
    required: bool = True
    description: str | None = None
    minimum_conditions: int | None = None
    source_ids: list[str] = Field(default_factory=list)
    conditions: list[PrerequisiteCondition] = Field(default_factory=list)


class Program(FrozenModel):
    id: str
    institution_id: str
    name: str
    degree_type: str | None = None
    program_type: str | None = None
    catalog_year: str | None = None
    active: bool = True


class ProgramRequirement(FrozenModel):
    id: str
    program_id: str
    parent_requirement_id: str | None = None
    requirement_type: RequirementType
    name: str
    minimum_courses: int | None = None
    minimum_credits: float | None = None
    required: bool = True
    source_ids: list[str] = Field(default_factory=list)


class RequirementCourseOption(FrozenModel):
    id: str
    program_requirement_id: str
    course_id: str
    option_group: str | None = None
    priority: int = 0
    source_ids: list[str] = Field(default_factory=list)


class GeneralEducationMapping(FrozenModel):
    id: str
    course_id: str
    institution_id: str
    category_code: str
    category_name: str | None = None
    status: str
    confidence: Confidence
    source_ids: list[str] = Field(default_factory=list)


class CourseEquivalency(FrozenModel):
    id: str
    source_course_id: str
    target_institution_id: str
    target_course_id: str | None = None
    equivalency_type: EquivalencyType
    credits_awarded: float | None = None
    confidence: Confidence
    effective_start_date: str | None = None
    effective_end_date: str | None = None
    source_ids: list[str] = Field(default_factory=list)


class StudentCourse(FrozenModel):
    id: str
    course_id: str | None = None
    institution_id: str
    course_code_raw: str
    credits_earned: float | None = None
    grade: str | None = None
    grade_points: float | None = None
    status: StudentCourseStatus
    term_completed: str | None = None


class ScenarioProgram(FrozenModel):
    program_id: str
    priority: int = Field(default=1, ge=1)


class PlanningScenario(FrozenModel):
    id: str
    user_id: str
    name: str | None = None
    current_institution_id: str
    target_term: str | None = None
    max_credits: float | None = None
    residency_status: str | None = None
    institution_type: str | None = None
    graduation_target: str | None = None
    selected_programs: list[ScenarioProgram] = Field(default_factory=list)
    selected_institution_ids: list[str] = Field(default_factory=list)


class RecommendationWeightConfig(FrozenModel):
    config_name: str = "default-v1"
    version: int = 1
    major_coverage_weight: float = 30
    university_coverage_weight: float = 20
    unlock_weight: float = 18
    dual_requirement_weight: float = 12
    graduation_acceleration_weight: float = 10
    infrequent_offering_weight: float = 8
    uncertain_equivalency_penalty: float = 15
    dead_end_penalty: float = 8
    duplicate_credit_penalty: float = 25

    @property
    def version_key(self) -> str:
        return f"{self.config_name}:{self.version}"


class ScenarioDataset(BaseModel):
    scenario: PlanningScenario
    courses: list[Course]
    offerings: list[CourseOffering]
    prerequisite_groups: list[PrerequisiteGroup]
    programs: list[Program]
    program_requirements: list[ProgramRequirement]
    requirement_course_options: list[RequirementCourseOption]
    general_education_mappings: list[GeneralEducationMapping]
    equivalencies: list[CourseEquivalency]
    student_courses: list[StudentCourse]
    weight_config: RecommendationWeightConfig = Field(default_factory=RecommendationWeightConfig)
    placement_results: dict[str, float] = Field(default_factory=dict)
    admitted_program_ids: set[str] = Field(default_factory=set)
    academic_data_version: str = "sample-v1"
    data_warnings: list[str] = Field(default_factory=list)


class CompletedCourse(FrozenModel):
    course_id: str
    grade_points: float | None = None
    credits_earned: float = 0


class CourseEligibilityResult(BaseModel):
    eligible: bool
    eligible_with_concurrent_enrollment: bool
    satisfied_groups: list[str] = Field(default_factory=list)
    unsatisfied_groups: list[str] = Field(default_factory=list)
    missing_courses: list[str] = Field(default_factory=list)
    minimum_grade_failures: list[str] = Field(default_factory=list)
    placement_alternatives: list[str] = Field(default_factory=list)
    permission_requirements: list[str] = Field(default_factory=list)
    confidence: str


class CandidateCourse(FrozenModel):
    course: Course
    eligibility: CourseEligibilityResult
    uncertain: bool = False


class CourseRecommendationFeatures(BaseModel):
    course_id: str
    selected_programs_helped: int
    selected_institutions_helped: int
    requirements_satisfied: list[str] = Field(default_factory=list)
    general_education_categories_satisfied: list[str] = Field(default_factory=list)
    directly_unlocked_courses: list[str] = Field(default_factory=list)
    descendant_courses_unlocked: list[str] = Field(default_factory=list)
    required_descendants_unlocked: list[str] = Field(default_factory=list)
    dependency_depth_reduction: int
    estimated_graduation_terms_saved: int
    offered_infrequently: bool
    equivalency_confidence: str
    duplicate_credit_risk: bool
    dead_end_risk: float = Field(ge=0, le=1)
    scenario_priorities_helped: list[int] = Field(default_factory=list)
    university_coverage: dict[str, list[str]] = Field(default_factory=dict)
    dead_end_factors: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)


class CourseRecommendation(BaseModel):
    course_id: str
    course_code: str
    title: str
    score: float
    rank: int
    eligibility: CourseEligibilityResult
    features: CourseRecommendationFeatures
    score_breakdown: dict[str, float]
    usefulness_label: str
    risk_level: str
    reasons: list[str]
    warnings: list[str]
    source_ids: list[str]


class ExcludedCourse(BaseModel):
    course_id: str
    course_code: str
    reason: str


class RecommendationRequest(BaseModel):
    target_term: str
    max_results: int = Field(default=10, ge=1, le=50)
    include_uncertain: bool = False


class RecommendationResponse(BaseModel):
    scenario_id: str
    target_term: str
    recommendations: list[CourseRecommendation]
    excluded_courses: list[ExcludedCourse]
    data_warnings: list[str]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    scenario_fingerprint: str
    cache_hit: bool = False


class RecommendationExplanationContext(BaseModel):
    student_goal_summary: str
    recommendation: CourseRecommendation
    selected_program_names: list[str]
    selected_institution_names: list[str]
    verified_source_summaries: list[str]


JsonObject = dict[str, Any]
