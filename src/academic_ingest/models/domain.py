from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from academic_ingest.models.enums import (
    ApplicantType,
    AuthorityTier,
    CalendarSystem,
    ConfidenceTier,
    ConflictStatus,
    CreditType,
    JobStatus,
    MajorType,
    OfferingStatus,
    PolicyFamily,
    RequirementType,
    ReviewStatus,
    Severity,
    SourceType,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


class EffectivePeriod(BaseModel):
    effective_from: datetime | None = None
    effective_to: datetime | None = None

    @model_validator(mode="after")
    def dates_are_ordered(self) -> EffectivePeriod:
        if self.effective_from and self.effective_to and self.effective_to < self.effective_from:
            raise ValueError("effective_to must be on or after effective_from")
        return self


class Institution(BaseModel):
    id: str
    legal_name: str
    common_name: str
    campus: str
    state: str
    country: str = "US"
    calendar_system: CalendarSystem
    official_domains: list[str]


class CatalogVersion(EffectivePeriod):
    id: UUID = Field(default_factory=uuid4)
    institution_id: str
    academic_year: str | None = None
    source_url: str
    retrieved_at: datetime = Field(default_factory=utc_now)
    superseded: bool = False
    confidence: ConfidenceTier = ConfidenceTier.NEEDS_REVIEW


class SourcePage(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    institution_id: str
    canonical_url: str
    final_url: str
    page_title: str
    source_type: SourceType
    policy_family: PolicyFamily
    campus: str
    http_status: int = Field(ge=100, le=599)
    content_type: str
    language: str = "en"
    first_seen_at: datetime = Field(default_factory=utc_now)
    last_seen_at: datetime = Field(default_factory=utc_now)


class SourceSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    source_page_id: UUID
    crawl_job_id: UUID
    retrieved_at: datetime = Field(default_factory=utc_now)
    raw_content_location: str
    raw_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    normalized_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    response_headers: dict[str, str] = Field(default_factory=dict)
    etag: str | None = None
    last_modified: str | None = None
    parser_version: str


class EvidenceRecord(EffectivePeriod):
    id: UUID = Field(default_factory=uuid4)
    source_snapshot_id: UUID
    source_url: str
    page_title: str
    evidence_text: str = Field(min_length=1)
    evidence_start: int | None = Field(default=None, ge=0)
    evidence_end: int | None = Field(default=None, ge=0)
    css_selector: str | None = None
    xpath: str | None = None
    table_identifier: str | None = None
    row_identifier: str | None = None
    heading_context: str | None = None
    footnote_context: str | None = None
    retrieved_at: datetime = Field(default_factory=utc_now)
    catalog_year: str | None = None
    parser_name: str
    parser_version: str
    authority_tier: AuthorityTier
    confidence_tier: ConfidenceTier
    reviewer_status: ReviewStatus = ReviewStatus.PENDING

    @model_validator(mode="after")
    def offsets_are_ordered(self) -> EvidenceRecord:
        if (
            self.evidence_start is not None
            and self.evidence_end is not None
            and self.evidence_end < self.evidence_start
        ):
            raise ValueError("evidence_end must be on or after evidence_start")
        return self


class EvidenceBackedRecord(EffectivePeriod):
    id: UUID = Field(default_factory=uuid4)
    institution_id: str
    campus: str = "Seattle"
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    unresolved_fields: list[str] = Field(default_factory=list)
    parser_name: str = "unassigned"
    parser_version: str = "0"
    crawl_job_id: UUID | None = None
    authority_tier: AuthorityTier = AuthorityTier.SECONDARY_OFFICIAL
    confidence_tier: ConfidenceTier = ConfidenceTier.UNRESOLVED
    review_status: ReviewStatus = ReviewStatus.PENDING


class Course(EvidenceBackedRecord):
    subject: str
    number: str
    canonical_code: str = ""
    title: str
    description: str = ""
    credits_min: Decimal = Field(ge=0)
    credits_max: Decimal = Field(ge=0)
    credit_type: CreditType = CreditType.QUARTER
    level: int | None = None
    prerequisite_expression_id: UUID | None = None
    corequisite_expression_id: UUID | None = None
    prerequisite_text: str | None = None
    corequisite_text: str | None = None
    restrictions: list[str] = Field(default_factory=list)
    repeatability: str | None = None
    equivalent_courses: list[str] = Field(default_factory=list)
    overlapping_courses: list[str] = Field(default_factory=list)
    general_education_designators: list[str] = Field(default_factory=list)
    historical_offering_notes: list[str] = Field(default_factory=list)
    catalog_version_id: UUID | None = None

    @model_validator(mode="after")
    def derive_and_validate_course_fields(self) -> Course:
        if self.credits_max < self.credits_min:
            raise ValueError("credits_max must be greater than or equal to credits_min")
        self.subject = " ".join(self.subject.upper().split())
        self.number = self.number.upper().strip()
        self.canonical_code = f"{self.subject} {self.number}"
        if self.level is None and self.number[:1].isdigit():
            self.level = int(self.number[0]) * 100
        return self


class Program(EvidenceBackedRecord):
    official_name: str
    degree_type: str | None = None
    college_or_school: str | None = None
    department: str | None = None
    major_type: MajorType = MajorType.UNKNOWN
    admission_path: str | None = None
    capacity_status: str | None = None
    application_required: bool | None = None
    application_terms: list[str] = Field(default_factory=list)
    application_deadlines: list[str] = Field(default_factory=list)
    minimum_gpa: Decimal | None = Field(default=None, ge=0, le=4)
    prerequisite_expression_id: UUID | None = None
    degree_requirements: list[UUID] = Field(default_factory=list)
    source_scope: str | None = None


class Requirement(EvidenceBackedRecord):
    program_id: UUID | None = None
    requirement_type: RequirementType
    name: str
    description: str = ""
    expression_id: UUID | None = None
    minimum_credits: Decimal | None = Field(default=None, ge=0)
    minimum_courses: int | None = Field(default=None, ge=0)
    minimum_grade: Decimal | None = Field(default=None, ge=0, le=4)
    allowed_courses: list[str] = Field(default_factory=list)
    double_counting_rule: str | None = None
    residency_rule: str | None = None
    mandatory: bool = False
    recommended: bool = False

    @model_validator(mode="after")
    def recommendation_is_not_mandatory(self) -> Requirement:
        if self.mandatory and self.recommended:
            raise ValueError("a requirement cannot be both mandatory and recommended")
        return self


class AdmissionsRule(EvidenceBackedRecord):
    applicant_type: ApplicantType
    rule_type: str
    value: str
    timing: str | None = None
    audience: str | None = None
    conditions: dict[str, Any] = Field(default_factory=dict)


class TransferPolicy(EvidenceBackedRecord):
    policy_type: str
    applicant_type: ApplicantType = ApplicantType.TRANSFER
    sending_institution_type: str | None = None
    credit_limit: Decimal | None = Field(default=None, ge=0)
    course_level: str | None = None
    degree_applicability: str | None = None
    class_standing_effect: str | None = None
    conditions: dict[str, Any] = Field(default_factory=dict)
    exceptions: list[str] = Field(default_factory=list)


class ExamCreditRule(EvidenceBackedRecord):
    exam_type: str
    exam_name: str
    score_min: Decimal
    score_max: Decimal
    awarded_courses: list[str] = Field(default_factory=list)
    awarded_credit_values: list[Decimal | None] = Field(default_factory=list)
    general_education_designators: list[str] = Field(default_factory=list)
    placement_effect: str | None = None
    duplicate_credit_rule: str | None = None
    native_speaker_rule: str | None = None
    major_specific_applicability: str = "unknown"
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def scores_and_awards_align(self) -> ExamCreditRule:
        if self.score_max < self.score_min:
            raise ValueError("score_max must be greater than or equal to score_min")
        if self.awarded_credit_values and len(self.awarded_courses) != len(
            self.awarded_credit_values
        ):
            raise ValueError("awarded courses and credit values must have matching lengths")
        return self


class CourseOfferingObservation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    course_id: UUID
    term: str
    observed_at: datetime = Field(default_factory=utc_now)
    source_url: str
    offered: bool
    status: OfferingStatus
    historical_only: bool = True


class ConflictRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    institution_id: str
    record_type: str
    record_ids: list[UUID]
    conflict_type: str
    differing_fields: dict[str, list[Any]]
    source_authorities: list[AuthorityTier]
    effective_periods: list[EffectivePeriod]
    detected_at: datetime = Field(default_factory=utc_now)
    status: ConflictStatus = ConflictStatus.OPEN
    suggested_review_action: str


class ReviewTask(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    institution_id: str
    source_page_id: UUID | None = None
    record_type: str
    record_id: UUID | None = None
    reason: str
    severity: Severity
    unresolved_question: str
    recommended_office: str | None = None
    status: ReviewStatus = ReviewStatus.PENDING
    created_at: datetime = Field(default_factory=utc_now)
    resolved_at: datetime | None = None


class CrawlJob(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    institution_id: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    status: JobStatus = JobStatus.QUEUED
    configuration: dict[str, Any] = Field(default_factory=dict)
    parser_versions: dict[str, str] = Field(default_factory=dict)
    pages_discovered: int = Field(default=0, ge=0)
    pages_fetched: int = Field(default=0, ge=0)
    pages_skipped: int = Field(default=0, ge=0)
    records_created: int = Field(default=0, ge=0)
    records_updated: int = Field(default=0, ge=0)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class PipelineIssue(BaseModel):
    code: str
    message: str
    source_url: str | None = None
    severity: Severity = Severity.WARNING


class SkippedItem(BaseModel):
    source_url: str
    reason: str


class ParserMetrics(BaseModel):
    pages_attempted: int = Field(default=0, ge=0)
    parse_successes: int = Field(default=0, ge=0)
    parse_failures: int = Field(default=0, ge=0)
    records_extracted: int = Field(default=0, ge=0)
    gpt_fallback_calls: int = Field(default=0, ge=0)


class PipelineResult(BaseModel):
    records: list[Any] = Field(default_factory=list)
    warnings: list[PipelineIssue] = Field(default_factory=list)
    errors: list[PipelineIssue] = Field(default_factory=list)
    skipped_items: list[SkippedItem] = Field(default_factory=list)
    review_tasks: list[ReviewTask] = Field(default_factory=list)
    discovered_links: list[str] = Field(default_factory=list)
    source_snapshots: list[SourceSnapshot] = Field(default_factory=list)
    parser_metrics: ParserMetrics = Field(default_factory=ParserMetrics)
