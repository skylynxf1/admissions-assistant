from enum import StrEnum


class CalendarSystem(StrEnum):
    QUARTER = "quarter"
    SEMESTER = "semester"
    OTHER = "other"


class SourceType(StrEnum):
    COURSE_CATALOG = "course_catalog"
    COURSE_GLOSSARY = "course_glossary"
    COURSE_SCHEDULE = "course_schedule"
    ADMISSIONS = "admissions"
    MAJORS_INDEX = "majors_index"
    MAJOR_DETAIL = "major_detail"
    TRANSFER_POLICY = "transfer_policy"
    EXAM_CREDIT = "exam_credit"
    EQUIVALENCY_GUIDE = "equivalency_guide"
    PDF = "pdf"
    GENERIC_HTML = "generic_html"


class PolicyFamily(StrEnum):
    COURSE = "course"
    PROGRAM = "program"
    MAJOR_ADMISSION = "major_admission"
    ADMISSIONS = "admissions"
    TRANSFER_POLICY = "transfer_policy"
    EXAM_CREDIT = "exam_credit"
    GENERAL_EDUCATION = "general_education"
    COURSE_OFFERING = "course_offering"


class AuthorityTier(StrEnum):
    OFFICIAL_CATALOG = "official_catalog"
    OFFICIAL_ADMISSIONS = "official_admissions"
    OFFICIAL_DEPARTMENT = "official_department"
    OFFICIAL_REGISTRAR = "official_registrar"
    OFFICIAL_TRANSFER_GUIDE = "official_transfer_guide"
    SECONDARY_OFFICIAL = "secondary_official"


class ConfidenceTier(StrEnum):
    VERIFIED = "verified"
    HIGH_CONFIDENCE = "high_confidence"
    NEEDS_REVIEW = "needs_review"
    UNRESOLVED = "unresolved"
    DEPRECATED = "deprecated"


class ReviewStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    RESOLVED = "resolved"
    NOT_REQUIRED = "not_required"


class MajorType(StrEnum):
    OPEN = "open"
    MINIMUM_REQUIREMENTS = "minimum_requirements"
    CAPACITY_CONSTRAINED = "capacity_constrained"
    UNKNOWN = "unknown"


class MappingOutcome(StrEnum):
    TRANSFERABLE = "transferable"
    DIRECT_EQUIVALENT = "direct_equivalent"
    GENERAL_EDUCATION = "general_education"
    MAJOR_PREREQUISITE = "major_prerequisite"
    DEGREE_REQUIREMENT = "degree_requirement"
    ENROLLMENT_PREREQUISITE = "enrollment_prerequisite"
    TRANSFER_ADMISSION_ELIGIBILITY = "transfer_admission_eligibility"
    CLASS_STANDING = "class_standing"
    GRADUATION_CREDIT = "graduation_credit"
    ELECTIVE_ONLY = "elective_only"
    NOT_FOUND = "not_found"
    EXPLICIT_NO_CREDIT = "explicit_no_credit"


class OfferingStatus(StrEnum):
    OBSERVED = "observed"
    HISTORICAL = "historical"
    CURRENT_PUBLIC_SCHEDULE = "current_public_schedule"
    UNKNOWN_FUTURE = "unknown_future"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ConflictStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class RequirementType(StrEnum):
    ENROLLMENT_PREREQUISITE = "enrollment_prerequisite"
    MAJOR_ADMISSION = "major_admission"
    DEGREE = "degree"
    GENERAL_EDUCATION = "general_education"
    RESIDENCY = "residency"
    RECOMMENDED_PREPARATION = "recommended_preparation"


class ApplicantType(StrEnum):
    TRANSFER = "transfer"
    FIRST_YEAR = "first_year"
    POSTBACCALAUREATE = "postbaccalaureate"
    RUNNING_START = "running_start"
    INTERNATIONAL = "international"
    UNKNOWN = "unknown"


class CreditType(StrEnum):
    QUARTER = "quarter"
    SEMESTER = "semester"
    UNSPECIFIED = "unspecified"
