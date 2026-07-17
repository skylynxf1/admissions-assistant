from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from academic_ingest.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class InstitutionModel(Base):
    __tablename__ = "institutions"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    legal_name: Mapped[str] = mapped_column(String(255))
    common_name: Mapped[str] = mapped_column(String(255))
    campus: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(2), default="US")
    calendar_system: Mapped[str] = mapped_column(String(30))
    official_domains: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CatalogVersionModel(Base):
    __tablename__ = "catalog_versions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.id"), index=True)
    academic_year: Mapped[str | None] = mapped_column(String(30))
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_url: Mapped[str] = mapped_column(Text)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    superseded: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    confidence: Mapped[str] = mapped_column(String(30))


class CrawlJobModel(Base):
    __tablename__ = "crawl_jobs"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.id"), index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), index=True)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    parser_versions: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    pages_discovered: Mapped[int] = mapped_column(Integer, default=0)
    pages_fetched: Mapped[int] = mapped_column(Integer, default=0)
    pages_skipped: Mapped[int] = mapped_column(Integer, default=0)
    records_created: Mapped[int] = mapped_column(Integer, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, default=0)
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list)
    errors: Mapped[list[str]] = mapped_column(JSON, default=list)


class SourcePageModel(Base):
    __tablename__ = "source_pages"
    __table_args__ = (UniqueConstraint("institution_id", "canonical_url"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.id"), index=True)
    canonical_url: Mapped[str] = mapped_column(Text)
    final_url: Mapped[str] = mapped_column(Text)
    page_title: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(50), index=True)
    policy_family: Mapped[str] = mapped_column(String(50), index=True)
    campus: Mapped[str] = mapped_column(String(100), index=True)
    http_status: Mapped[int] = mapped_column(Integer)
    content_type: Mapped[str] = mapped_column(String(255))
    language: Mapped[str] = mapped_column(String(20), default="en")
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SourceSnapshotModel(Base):
    __tablename__ = "source_snapshots"
    __table_args__ = (UniqueConstraint("source_page_id", "raw_content_hash"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    source_page_id: Mapped[UUID] = mapped_column(ForeignKey("source_pages.id"), index=True)
    crawl_job_id: Mapped[UUID] = mapped_column(ForeignKey("crawl_jobs.id"), index=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    raw_content_location: Mapped[str] = mapped_column(Text)
    raw_content_hash: Mapped[str] = mapped_column(String(64), index=True)
    normalized_content_hash: Mapped[str] = mapped_column(String(64), index=True)
    response_headers: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    etag: Mapped[str | None] = mapped_column(Text)
    last_modified: Mapped[str | None] = mapped_column(Text)
    parser_version: Mapped[str] = mapped_column(String(100))


class SourceChangeEventModel(Base):
    __tablename__ = "source_change_events"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    source_page_id: Mapped[UUID] = mapped_column(ForeignKey("source_pages.id"), index=True)
    previous_snapshot_id: Mapped[UUID] = mapped_column(ForeignKey("source_snapshots.id"))
    current_snapshot_id: Mapped[UUID] = mapped_column(ForeignKey("source_snapshots.id"))
    changed_blocks: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    material: Mapped[bool] = mapped_column(Boolean, default=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class EvidenceRecordModel(Base):
    __tablename__ = "evidence_records"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    source_snapshot_id: Mapped[UUID] = mapped_column(ForeignKey("source_snapshots.id"), index=True)
    source_url: Mapped[str] = mapped_column(Text)
    page_title: Mapped[str] = mapped_column(Text)
    evidence_text: Mapped[str] = mapped_column(Text)
    evidence_start: Mapped[int | None] = mapped_column(Integer)
    evidence_end: Mapped[int | None] = mapped_column(Integer)
    css_selector: Mapped[str | None] = mapped_column(Text)
    xpath: Mapped[str | None] = mapped_column(Text)
    table_identifier: Mapped[str | None] = mapped_column(Text)
    row_identifier: Mapped[str | None] = mapped_column(Text)
    heading_context: Mapped[str | None] = mapped_column(Text)
    footnote_context: Mapped[str | None] = mapped_column(Text)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    catalog_year: Mapped[str | None] = mapped_column(String(30))
    parser_name: Mapped[str] = mapped_column(String(100))
    parser_version: Mapped[str] = mapped_column(String(100))
    authority_tier: Mapped[str] = mapped_column(String(50))
    confidence_tier: Mapped[str] = mapped_column(String(50))
    reviewer_status: Mapped[str] = mapped_column(String(50))


class RequirementExpressionModel(Base):
    __tablename__ = "requirement_expressions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.id"), index=True)
    node_type: Mapped[str] = mapped_column(String(50), index=True)
    expression: Mapped[dict[str, Any]] = mapped_column(JSON)
    original_source_text: Mapped[str] = mapped_column(Text)
    evidence_record_id: Mapped[UUID | None] = mapped_column(ForeignKey("evidence_records.id"))
    parse_confidence: Mapped[str] = mapped_column(String(50))
    unresolved_warning: Mapped[str | None] = mapped_column(Text)


class VersionedPolicyMixin:
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    superseded: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    evidence_record_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list)
    unresolved_fields: Mapped[list[str]] = mapped_column(JSON, default=list)
    confidence_tier: Mapped[str] = mapped_column(String(50), index=True)
    review_status: Mapped[str] = mapped_column(String(50), index=True)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CourseModel(VersionedPolicyMixin, Base):
    __tablename__ = "courses"
    __table_args__ = (UniqueConstraint("institution_id", "canonical_code", "version_number"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.id"), index=True)
    campus: Mapped[str] = mapped_column(String(100), index=True)
    subject: Mapped[str] = mapped_column(String(30), index=True)
    number: Mapped[str] = mapped_column(String(20), index=True)
    canonical_code: Mapped[str] = mapped_column(String(60), index=True)
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    credits_min: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    credits_max: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    credit_type: Mapped[str] = mapped_column(String(30))
    level: Mapped[int | None] = mapped_column(Integer)
    prerequisite_expression_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("requirement_expressions.id")
    )
    corequisite_expression_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("requirement_expressions.id")
    )
    restrictions: Mapped[list[str]] = mapped_column(JSON, default=list)
    repeatability: Mapped[str | None] = mapped_column(Text)
    equivalent_courses: Mapped[list[str]] = mapped_column(JSON, default=list)
    overlapping_courses: Mapped[list[str]] = mapped_column(JSON, default=list)
    general_education_designators: Mapped[list[str]] = mapped_column(JSON, default=list)
    historical_offering_notes: Mapped[list[str]] = mapped_column(JSON, default=list)
    catalog_version_id: Mapped[UUID | None] = mapped_column(ForeignKey("catalog_versions.id"))


class ProgramModel(VersionedPolicyMixin, Base):
    __tablename__ = "programs"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.id"), index=True)
    campus: Mapped[str] = mapped_column(String(100), index=True)
    official_name: Mapped[str] = mapped_column(Text, index=True)
    degree_type: Mapped[str | None] = mapped_column(String(100))
    college_or_school: Mapped[str | None] = mapped_column(Text)
    department: Mapped[str | None] = mapped_column(Text)
    major_type: Mapped[str] = mapped_column(String(50), index=True)
    admission_path: Mapped[str | None] = mapped_column(Text)
    capacity_status: Mapped[str | None] = mapped_column(Text)
    application_required: Mapped[bool | None] = mapped_column(Boolean)
    application_terms: Mapped[list[str]] = mapped_column(JSON, default=list)
    application_deadlines: Mapped[list[str]] = mapped_column(JSON, default=list)
    minimum_gpa: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    prerequisite_expression_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("requirement_expressions.id")
    )
    degree_requirements: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_scope: Mapped[str | None] = mapped_column(Text)


class RequirementModel(VersionedPolicyMixin, Base):
    __tablename__ = "requirements"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.id"), index=True)
    program_id: Mapped[UUID | None] = mapped_column(ForeignKey("programs.id"), index=True)
    requirement_type: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    expression_id: Mapped[UUID | None] = mapped_column(ForeignKey("requirement_expressions.id"))
    minimum_credits: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    minimum_courses: Mapped[int | None] = mapped_column(Integer)
    minimum_grade: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    allowed_courses: Mapped[list[str]] = mapped_column(JSON, default=list)
    double_counting_rule: Mapped[str | None] = mapped_column(Text)
    residency_rule: Mapped[str | None] = mapped_column(Text)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=False)
    recommended: Mapped[bool] = mapped_column(Boolean, default=False)


class AdmissionsRuleModel(VersionedPolicyMixin, Base):
    __tablename__ = "admissions_rules"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.id"), index=True)
    campus: Mapped[str] = mapped_column(String(100), index=True)
    applicant_type: Mapped[str] = mapped_column(String(50), index=True)
    rule_type: Mapped[str] = mapped_column(String(100), index=True)
    value: Mapped[str] = mapped_column(Text)
    timing: Mapped[str | None] = mapped_column(Text)
    audience: Mapped[str | None] = mapped_column(Text)
    conditions: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class TransferPolicyModel(VersionedPolicyMixin, Base):
    __tablename__ = "transfer_policies"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.id"), index=True)
    policy_type: Mapped[str] = mapped_column(String(100), index=True)
    applicant_type: Mapped[str] = mapped_column(String(50), index=True)
    sending_institution_type: Mapped[str | None] = mapped_column(String(100))
    credit_limit: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    course_level: Mapped[str | None] = mapped_column(String(100))
    degree_applicability: Mapped[str | None] = mapped_column(Text)
    class_standing_effect: Mapped[str | None] = mapped_column(Text)
    conditions: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    exceptions: Mapped[list[str]] = mapped_column(JSON, default=list)


class ExamCreditRuleModel(VersionedPolicyMixin, Base):
    __tablename__ = "exam_credit_rules"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.id"), index=True)
    exam_type: Mapped[str] = mapped_column(String(50), index=True)
    exam_name: Mapped[str] = mapped_column(Text, index=True)
    score_min: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    score_max: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    awarded_courses: Mapped[list[str]] = mapped_column(JSON, default=list)
    awarded_credit_values: Mapped[list[float | None]] = mapped_column(JSON, default=list)
    general_education_designators: Mapped[list[str]] = mapped_column(JSON, default=list)
    placement_effect: Mapped[str | None] = mapped_column(Text)
    duplicate_credit_rule: Mapped[str | None] = mapped_column(Text)
    native_speaker_rule: Mapped[str | None] = mapped_column(Text)
    major_specific_applicability: Mapped[str] = mapped_column(String(100), default="unknown")
    notes: Mapped[list[str]] = mapped_column(JSON, default=list)


class CourseOfferingObservationModel(Base):
    __tablename__ = "course_offering_observations"
    __table_args__ = (UniqueConstraint("course_id", "term", "source_url"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id"), index=True)
    term: Mapped[str] = mapped_column(String(30), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    source_url: Mapped[str] = mapped_column(Text)
    offered: Mapped[bool] = mapped_column(Boolean)
    status: Mapped[str] = mapped_column(String(50))
    historical_only: Mapped[bool] = mapped_column(Boolean, default=True)


class ConflictRecordModel(Base):
    __tablename__ = "conflict_records"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.id"), index=True)
    record_type: Mapped[str] = mapped_column(String(100), index=True)
    record_ids: Mapped[list[str]] = mapped_column(JSON)
    conflict_type: Mapped[str] = mapped_column(String(100), index=True)
    differing_fields: Mapped[dict[str, Any]] = mapped_column(JSON)
    source_authorities: Mapped[list[str]] = mapped_column(JSON)
    effective_periods: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    status: Mapped[str] = mapped_column(String(50), index=True)
    suggested_review_action: Mapped[str] = mapped_column(Text)


class ReviewTaskModel(Base):
    __tablename__ = "review_tasks"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.id"), index=True)
    source_page_id: Mapped[UUID | None] = mapped_column(ForeignKey("source_pages.id"), index=True)
    record_type: Mapped[str] = mapped_column(String(100), index=True)
    record_id: Mapped[UUID | None] = mapped_column(Uuid, index=True)
    reason: Mapped[str] = mapped_column(String(255), index=True)
    severity: Mapped[str] = mapped_column(String(50), index=True)
    unresolved_question: Mapped[str] = mapped_column(Text)
    recommended_office: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class RecordVersionModel(Base):
    __tablename__ = "record_versions"
    __table_args__ = (
        UniqueConstraint("record_type", "canonical_key", "version_number"),
        UniqueConstraint("record_type", "canonical_key", "content_hash"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    record_type: Mapped[str] = mapped_column(String(100), index=True)
    canonical_key: Mapped[str] = mapped_column(Text, index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    evidence_record_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    superseded: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
