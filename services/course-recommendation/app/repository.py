from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Protocol

from app.models import (
    Confidence,
    ConditionType,
    Course,
    CourseEquivalency,
    CourseOffering,
    EquivalencyType,
    GeneralEducationMapping,
    GroupType,
    OfferingStatus,
    PlanningScenario,
    PrerequisiteCondition,
    PrerequisiteGroup,
    Program,
    ProgramRequirement,
    RecommendationResponse,
    RecommendationWeightConfig,
    RequirementCourseOption,
    RequirementType,
    ScenarioDataset,
    ScenarioProgram,
    StudentCourse,
    StudentCourseStatus,
)


class ScenarioNotFoundError(LookupError):
    pass


class RecommendationRepository(Protocol):
    async def load_dataset(self, scenario_id: str) -> ScenarioDataset: ...

    async def get_cached(
        self, scenario_id: str, target_term: str, fingerprint: str
    ) -> RecommendationResponse | None: ...

    async def save_cached(self, response: RecommendationResponse, weight_version: str, academic_version: str) -> None: ...


class InMemoryRecommendationRepository:
    def __init__(self, datasets: dict[str, ScenarioDataset]) -> None:
        self.datasets = datasets
        self.cache: dict[tuple[str, str, str], RecommendationResponse] = {}

    async def load_dataset(self, scenario_id: str) -> ScenarioDataset:
        try:
            return self.datasets[scenario_id].model_copy(deep=True)
        except KeyError as error:
            raise ScenarioNotFoundError(scenario_id) from error

    async def get_cached(
        self, scenario_id: str, target_term: str, fingerprint: str
    ) -> RecommendationResponse | None:
        cached = self.cache.get((scenario_id, target_term, fingerprint))
        return cached.model_copy(update={"cache_hit": True}, deep=True) if cached else None

    async def save_cached(self, response: RecommendationResponse, weight_version: str, academic_version: str) -> None:
        del weight_version, academic_version
        self.cache[(response.scenario_id, response.target_term, response.scenario_fingerprint)] = response


class SupabaseRecommendationRepository:
    """Supabase/PostgREST data adapter; all recommendation logic stays outside it."""

    def __init__(self, client: Any) -> None:
        self.client = client

    @classmethod
    def from_env(cls) -> "SupabaseRecommendationRepository":
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required.")
        from supabase import create_client

        return cls(create_client(url, key))

    def _rows(self, schema: str, table: str, *, columns: str = "*") -> Any:
        return self.client.schema(schema).table(table).select(columns)

    async def load_dataset(self, scenario_id: str) -> ScenarioDataset:
        scenario_rows = self._rows("planning", "scenarios").eq("id", scenario_id).limit(1).execute().data
        if not scenario_rows:
            raise ScenarioNotFoundError(scenario_id)
        scenario_row = scenario_rows[0]
        targets = self._rows("planning", "scenario_targets").eq("scenario_id", scenario_id).execute().data
        selected_programs = [
            ScenarioProgram(program_id=row["program_id"], priority=row.get("priority") or 1)
            for row in targets
            if row.get("program_id")
        ]
        program_ids = [item.program_id for item in selected_programs]
        selected_institution_ids = sorted({
            row["institution_id"] for row in targets if row.get("institution_id")
        })
        current_institution_id = scenario_row.get("current_institution_id")
        if not current_institution_id:
            snapshot = scenario_row.get("profile_snapshot") or {}
            current_institution_id = snapshot.get("currentInstitutionId")
        if not current_institution_id:
            raise ValueError("Scenario is missing current_institution_id.")

        programs_rows = self._rows("catalog", "programs").in_("id", program_ids).execute().data if program_ids else []
        programs = [Program(**self._only(Program, row)) for row in programs_rows]
        selected_institution_ids = sorted(set(selected_institution_ids) | {item.institution_id for item in programs})

        course_rows = self._rows("catalog", "recommendation_courses").execute().data
        courses = [Course(**self._only(Course, row)) for row in course_rows]
        course_ids = [course.id for course in courses]
        offering_rows = self._rows("catalog", "course_offerings").in_("course_id", course_ids).execute().data if course_ids else []
        offerings = [
            CourseOffering(
                id=row["id"],
                course_id=row["course_id"],
                academic_year=row.get("academic_year"),
                term_name=row.get("term") or "unknown",
                offering_status=self._offering_status(row),
                campus=row.get("campus"),
                delivery_mode=row.get("delivery_mode"),
                source_ids=self._source_ids(row),
            )
            for row in offering_rows
        ]

        group_rows = self._rows("policy", "course_prerequisite_groups").execute().data
        condition_rows = self._rows("policy", "course_prerequisite_conditions").execute().data
        conditions_by_group: dict[str, list[PrerequisiteCondition]] = {}
        for row in condition_rows:
            condition = PrerequisiteCondition(
                **self._only(PrerequisiteCondition, row),
                source_ids=self._source_ids(row),
            )
            conditions_by_group.setdefault(condition.prerequisite_group_id, []).append(condition)
        prerequisite_groups = [
            PrerequisiteGroup(
                **self._only(PrerequisiteGroup, row, exclude={"conditions", "source_ids"}),
                source_ids=self._source_ids(row),
                conditions=conditions_by_group.get(row["id"], []),
            )
            for row in group_rows
        ]

        requirement_rows = (
            self._rows("policy", "requirements").in_("program_id", program_ids).execute().data
            if program_ids else []
        )
        requirements = [self._program_requirement(row) for row in requirement_rows]
        requirement_ids = [item.id for item in requirements]
        option_rows = (
            self._rows("policy", "requirement_courses").in_("requirement_id", requirement_ids).execute().data
            if requirement_ids else []
        )
        options = [
            RequirementCourseOption(
                id=f"{row['requirement_id']}:{row['course_id']}:{row.get('role', 'allowed')}",
                program_requirement_id=row["requirement_id"],
                course_id=row["course_id"],
                option_group=row.get("option_group"),
                priority=row.get("priority") or 0,
                source_ids=self._source_ids(row),
            )
            for row in option_rows
        ]

        ge_rows = self._rows("policy", "general_education_mappings").execute().data
        ge_mappings = [
            GeneralEducationMapping(**self._only(GeneralEducationMapping, row, exclude={"source_ids"}), source_ids=self._source_ids(row))
            for row in ge_rows
        ]
        equivalency_rows = self._rows("equivalency", "recommendation_course_equivalencies").execute().data
        equivalencies = [CourseEquivalency(**self._only(CourseEquivalency, row)) for row in equivalency_rows]

        student_rows = self._rows("student", "student_courses").eq("user_id", scenario_row["user_id"]).execute().data
        student_courses = [self._student_course(row, courses, current_institution_id) for row in student_rows]
        weight_rows = self._rows("planning", "recommendation_weight_configs").eq("active", True).limit(1).execute().data
        weight_config = RecommendationWeightConfig(**self._only(RecommendationWeightConfig, weight_rows[0])) if weight_rows else RecommendationWeightConfig()

        scenario = PlanningScenario(
            id=scenario_id,
            user_id=scenario_row["user_id"],
            name=scenario_row.get("name"),
            current_institution_id=current_institution_id,
            target_term=scenario_row.get("target_term"),
            max_credits=float(scenario_row["max_credits"]) if scenario_row.get("max_credits") is not None else None,
            residency_status=scenario_row.get("residency_status"),
            institution_type=scenario_row.get("institution_type"),
            graduation_target=scenario_row.get("graduation_target"),
            selected_programs=selected_programs,
            selected_institution_ids=selected_institution_ids,
        )
        data_version = self._data_version(course_rows, group_rows, condition_rows, requirement_rows, equivalency_rows)
        return ScenarioDataset(
            scenario=scenario,
            courses=courses,
            offerings=offerings,
            prerequisite_groups=prerequisite_groups,
            programs=programs,
            program_requirements=requirements,
            requirement_course_options=options,
            general_education_mappings=ge_mappings,
            equivalencies=equivalencies,
            student_courses=student_courses,
            weight_config=weight_config,
            academic_data_version=data_version,
        )

    async def get_cached(
        self, scenario_id: str, target_term: str, fingerprint: str
    ) -> RecommendationResponse | None:
        rows = (
            self._rows("planning", "recommendation_cache", columns="response")
            .eq("scenario_id", scenario_id)
            .eq("target_term", target_term)
            .eq("fingerprint", fingerprint)
            .limit(1)
            .execute()
            .data
        )
        return RecommendationResponse.model_validate(rows[0]["response"]).model_copy(update={"cache_hit": True}) if rows else None

    async def save_cached(self, response: RecommendationResponse, weight_version: str, academic_version: str) -> None:
        self.client.schema("planning").table("recommendation_cache").upsert(
            {
                "scenario_id": response.scenario_id,
                "target_term": response.target_term,
                "fingerprint": response.scenario_fingerprint,
                "weight_config_version": weight_version,
                "academic_data_version": academic_version,
                "response": response.model_dump(mode="json"),
            },
            on_conflict="scenario_id,target_term,fingerprint",
        ).execute()

    @staticmethod
    def _only(model: type[Any], row: dict[str, Any], exclude: set[str] | None = None) -> dict[str, Any]:
        allowed = set(model.model_fields) - (exclude or set())
        return {key: value for key, value in row.items() if key in allowed and value is not None}

    @staticmethod
    def _source_ids(row: dict[str, Any]) -> list[str]:
        values = row.get("source_ids") or ([row["source_id"]] if row.get("source_id") else [])
        return sorted({str(value) for value in values if value})

    @staticmethod
    def _offering_status(row: dict[str, Any]) -> OfferingStatus:
        value = row.get("offering_status") or row.get("status") or "UNKNOWN"
        normalized = str(value).upper().replace("-", "_").replace(" ", "_")
        return OfferingStatus(normalized) if normalized in OfferingStatus._value2member_map_ else OfferingStatus.UNKNOWN

    @staticmethod
    def _student_course(
        row: dict[str, Any], courses: list[Course], current_institution_id: str
    ) -> StudentCourse:
        raw_status = str(row.get("status") or "COMPLETED").upper()
        status = StudentCourseStatus(raw_status) if raw_status in StudentCourseStatus._value2member_map_ else StudentCourseStatus.COMPLETED
        institution_id = row.get("institution_id") or current_institution_id
        raw_code = " ".join(str(row.get("course_code_raw") or "").upper().split())
        course_id = row.get("course_id")
        if not course_id:
            course_id = next(
                (
                    course.id for course in courses
                    if course.institution_id == institution_id
                    and " ".join(course.course_code.upper().split()) == raw_code
                ),
                None,
            )
        grade_points = row.get("grade_points")
        if grade_points is None:
            grade_points = {
                "A+": 4.0, "A": 4.0, "A-": 3.7,
                "B+": 3.3, "B": 3.0, "B-": 2.7,
                "C+": 2.3, "C": 2.0, "C-": 1.7,
                "D+": 1.3, "D": 1.0, "F": 0.0,
            }.get(str(row.get("grade") or "").upper())
        return StudentCourse(
            id=row["id"],
            course_id=course_id,
            institution_id=institution_id,
            course_code_raw=row.get("course_code_raw") or "",
            credits_earned=float(row["credits_earned"]) if row.get("credits_earned") is not None else None,
            grade=row.get("grade"),
            grade_points=float(grade_points) if grade_points is not None else None,
            status=status,
            term_completed=row.get("term_completed"),
        )

    @staticmethod
    def _program_requirement(row: dict[str, Any]) -> ProgramRequirement:
        raw = str(row.get("requirement_type") or "other")
        mapped = {
            "general_education": RequirementType.GENERAL_EDUCATION,
            "major": RequirementType.COURSE_GROUP,
            "major_admission": RequirementType.COURSE_GROUP,
            "enrollment_prerequisite": RequirementType.SPECIFIC_COURSE,
            "graduation": RequirementType.OTHER,
        }.get(raw, RequirementType.OTHER)
        return ProgramRequirement(
            id=row["id"],
            program_id=row["program_id"],
            parent_requirement_id=row.get("parent_requirement_id"),
            requirement_type=mapped,
            name=row["name"],
            minimum_courses=row.get("minimum_courses"),
            minimum_credits=float(row["minimum_credits"]) if row.get("minimum_credits") is not None else None,
            required=row.get("mandatory", True),
            source_ids=SupabaseRecommendationRepository._source_ids(row),
        )

    @staticmethod
    def _data_version(*row_sets: list[dict[str, Any]]) -> str:
        keys = sorted(str(row.get("id")) for rows in row_sets for row in rows)
        return hashlib.sha256(json.dumps(keys, separators=(",", ":")).encode()).hexdigest()
