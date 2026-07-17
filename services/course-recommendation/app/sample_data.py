from __future__ import annotations

from app.models import (
    ConditionType,
    Confidence,
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
    RequirementCourseOption,
    RequirementType,
    ScenarioDataset,
    ScenarioProgram,
    StudentCourse,
    StudentCourseStatus,
)

SCENARIO_ID = "90000000-0000-0000-0000-000000000001"
BC = "10000000-0000-0000-0000-000000000004"
UW = "10000000-0000-0000-0000-000000000001"
BERKELEY = "10000000-0000-0000-0000-000000000002"


def sample_dataset() -> ScenarioDataset:
    courses = [
        _course("calc1", BC, "MATH& 151", "Calculus I", 5),
        _course("calc2", BC, "MATH& 152", "Calculus II", 5),
        _course("linear", BC, "MATH 208", "Linear Algebra", 5),
        _course("physics1", BC, "PHYS& 221", "Engineering Physics I", 5),
        _course("physics2", BC, "PHYS& 222", "Engineering Physics II", 5),
        _course("prog1", BC, "CS 141", "Programming I", 5),
        _course("data", BC, "CS 210", "Data Structures", 5),
        _course("writing", BC, "ENGL& 102", "Composition II", 5),
        _course("uw-calc2", UW, "MATH 125", "Calculus with Analytic Geometry II", 5),
        _course("uw-linear", UW, "MATH 208", "Matrix Algebra", 3),
        _course("uw-data", UW, "CSE 143", "Computer Programming II", 5),
        _course("uc-calc2", BERKELEY, "MATH 1B", "Calculus", 4),
    ]
    offerings = [
        *[_offering("calc2", term) for term in ("autumn", "winter", "spring")],
        _offering("linear", "winter"),
        _offering("physics1", "autumn"),
        _offering("physics2", "winter"),
        *[_offering("data", term) for term in ("autumn", "winter")],
        _offering("writing", "autumn"),
    ]
    groups = [
        _course_group("g-calc2", "calc2", "calc1"),
        _course_group("g-linear", "linear", "calc2"),
        _course_group("g-physics1", "physics1", "calc1"),
        _course_group("g-physics2", "physics2", "physics1"),
        PrerequisiteGroup(
            id="g-data-math",
            target_course_id="data",
            group_type=GroupType.ANY,
            group_order=0,
            conditions=[
                PrerequisiteCondition(
                    id="c-data-calc1",
                    prerequisite_group_id="g-data-math",
                    condition_type=ConditionType.COURSE,
                    prerequisite_course_id="calc1",
                    confidence=Confidence.HIGH,
                    source_ids=["src-data-prereq"],
                ),
                PrerequisiteCondition(
                    id="c-data-placement",
                    prerequisite_group_id="g-data-math",
                    condition_type=ConditionType.PLACEMENT,
                    placement_test_code="ALEKS",
                    minimum_placement_score=75,
                    confidence=Confidence.HIGH,
                    source_ids=["src-data-prereq"],
                ),
            ],
            source_ids=["src-data-prereq"],
        ),
        PrerequisiteGroup(
            id="g-data-programming",
            target_course_id="data",
            group_type=GroupType.ALL,
            group_order=1,
            conditions=[
                PrerequisiteCondition(
                    id="c-data-prog1",
                    prerequisite_group_id="g-data-programming",
                    condition_type=ConditionType.COURSE,
                    prerequisite_course_id="prog1",
                    minimum_grade_points=2.0,
                    confidence=Confidence.HIGH,
                    source_ids=["src-data-prereq"],
                )
            ],
            source_ids=["src-data-prereq"],
        ),
    ]
    programs = [
        Program(
            id="program-cs",
            institution_id=UW,
            name="Computer Science",
            degree_type="BS",
            program_type="major",
        ),
        Program(
            id="program-info",
            institution_id=UW,
            name="Informatics",
            degree_type="BS",
            program_type="major",
        ),
        Program(
            id="program-data",
            institution_id=BERKELEY,
            name="Data Science",
            degree_type="BA",
            program_type="major",
        ),
    ]
    requirements = [
        _requirement("req-cs-calc", "program-cs", "Calculus II"),
        _requirement("req-cs-data", "program-cs", "Programming sequence"),
        _requirement("req-info-calc", "program-info", "Quantitative preparation"),
        _requirement("req-data-calc", "program-data", "Calculus II"),
        _requirement("req-data-linear", "program-data", "Linear algebra"),
    ]
    options = [
        _option("req-cs-calc", "uw-calc2"),
        _option("req-cs-data", "uw-data"),
        _option("req-info-calc", "uw-calc2"),
        _option("req-data-calc", "uc-calc2"),
        _option("req-data-linear", "uw-linear"),
    ]
    equivalencies = [
        _equivalency("eq-calc2-uw", "calc2", UW, "uw-calc2", Confidence.HIGH),
        _equivalency("eq-calc2-uc", "calc2", BERKELEY, "uc-calc2", Confidence.MEDIUM),
        _equivalency("eq-linear-uw", "linear", UW, "uw-linear", Confidence.HIGH),
        _equivalency("eq-data-uw", "data", UW, "uw-data", Confidence.HIGH),
        CourseEquivalency(
            id="eq-writing-uc",
            source_course_id="writing",
            target_institution_id=BERKELEY,
            equivalency_type=EquivalencyType.GENERAL_ELECTIVE,
            confidence=Confidence.MEDIUM,
            source_ids=["src-eq-writing-uc"],
        ),
    ]
    ge = [
        _ge("ge-calc2-uw", "calc2", UW, "NSc", "Natural Sciences"),
        _ge("ge-calc2-uc", "calc2", BERKELEY, "QR", "Quantitative Reasoning"),
        _ge("ge-writing-uw", "writing", UW, "C", "Composition"),
        _ge("ge-writing-uc", "writing", BERKELEY, "R1B", "Reading and Composition"),
    ]
    student_courses = [
        StudentCourse(
            id="student-calc1",
            course_id="calc1",
            institution_id=BC,
            course_code_raw="MATH& 151",
            credits_earned=5,
            grade="A-",
            grade_points=3.7,
            status=StudentCourseStatus.COMPLETED,
            term_completed="spring-2026",
        ),
        StudentCourse(
            id="student-prog1",
            course_id="prog1",
            institution_id=BC,
            course_code_raw="CS 141",
            credits_earned=5,
            grade="B+",
            grade_points=3.3,
            status=StudentCourseStatus.COMPLETED,
            term_completed="spring-2026",
        ),
    ]
    return ScenarioDataset(
        scenario=PlanningScenario(
            id=SCENARIO_ID,
            user_id="sample-user",
            name="Sample multi-university transfer plan",
            current_institution_id=BC,
            target_term="autumn-2026",
            max_credits=15,
            residency_status="resident",
            institution_type="community-college",
            graduation_target="spring-2029",
            selected_programs=[
                ScenarioProgram(program_id="program-cs", priority=1),
                ScenarioProgram(program_id="program-info", priority=2),
                ScenarioProgram(program_id="program-data", priority=3),
            ],
            selected_institution_ids=[UW, BERKELEY],
        ),
        courses=courses,
        offerings=offerings,
        prerequisite_groups=groups,
        programs=programs,
        program_requirements=requirements,
        requirement_course_options=options,
        general_education_mappings=ge,
        equivalencies=equivalencies,
        student_courses=student_courses,
        academic_data_version="fictional-sample-v1",
        data_warnings=[
            "Sample data only: course rules, offerings, and equivalencies are fictional "
            "and are not verified official information."
        ],
    )


def _course(course_id: str, institution_id: str, code: str, title: str, credits: float) -> Course:
    return Course(
        id=course_id,
        institution_id=institution_id,
        course_code=code,
        subject_code=code.split()[0],
        course_number=code.split()[-1],
        title=title,
        credits_min=credits,
        credits_max=credits,
        credit_system="quarter",
        confidence=Confidence.HIGH,
        source_ids=[f"src-course-{course_id}"],
    )


def _offering(course_id: str, term: str) -> CourseOffering:
    return CourseOffering(
        id=f"offering-{course_id}-{term}",
        course_id=course_id,
        academic_year=2026,
        term_name=term,
        offering_status=OfferingStatus.TYPICALLY_OFFERED,
        source_ids=[f"src-offering-{course_id}-{term}"],
    )


def _course_group(group_id: str, target: str, prerequisite: str) -> PrerequisiteGroup:
    return PrerequisiteGroup(
        id=group_id,
        target_course_id=target,
        group_type=GroupType.ALL,
        conditions=[
            PrerequisiteCondition(
                id=f"condition-{group_id}",
                prerequisite_group_id=group_id,
                condition_type=ConditionType.COURSE,
                prerequisite_course_id=prerequisite,
                confidence=Confidence.HIGH,
                source_ids=[f"src-{group_id}"],
            )
        ],
        source_ids=[f"src-{group_id}"],
    )


def _requirement(requirement_id: str, program_id: str, name: str) -> ProgramRequirement:
    return ProgramRequirement(
        id=requirement_id,
        program_id=program_id,
        requirement_type=RequirementType.SPECIFIC_COURSE,
        name=name,
        source_ids=[f"src-{requirement_id}"],
    )


def _option(requirement_id: str, course_id: str) -> RequirementCourseOption:
    return RequirementCourseOption(
        id=f"option-{requirement_id}-{course_id}",
        program_requirement_id=requirement_id,
        course_id=course_id,
        source_ids=[f"src-{requirement_id}"],
    )


def _equivalency(
    equivalency_id: str,
    source_course_id: str,
    institution_id: str,
    target_course_id: str,
    confidence: Confidence,
) -> CourseEquivalency:
    return CourseEquivalency(
        id=equivalency_id,
        source_course_id=source_course_id,
        target_institution_id=institution_id,
        target_course_id=target_course_id,
        equivalency_type=EquivalencyType.DIRECT,
        confidence=confidence,
        source_ids=[f"src-{equivalency_id}"],
    )


def _ge(
    mapping_id: str,
    course_id: str,
    institution_id: str,
    category_code: str,
    category_name: str,
) -> GeneralEducationMapping:
    return GeneralEducationMapping(
        id=mapping_id,
        course_id=course_id,
        institution_id=institution_id,
        category_code=category_code,
        category_name=category_name,
        status="CONFIRMED",
        confidence=Confidence.HIGH,
        source_ids=[f"src-{mapping_id}"],
    )
