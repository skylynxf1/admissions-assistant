from __future__ import annotations

from academic_ingest.models.domain import (
    AdmissionsRule,
    Course,
    EvidenceBackedRecord,
    ExamCreditRule,
    Program,
    Requirement,
    TransferPolicy,
)

PolicyRecord = Course | Program | Requirement | AdmissionsRule | TransferPolicy | ExamCreditRule


def record_type_name(record: EvidenceBackedRecord) -> str:
    names = {
        Course: "course",
        Program: "program",
        Requirement: "requirement",
        AdmissionsRule: "admissions_rule",
        TransferPolicy: "transfer_policy",
        ExamCreditRule: "exam_credit_rule",
    }
    return names.get(type(record), type(record).__name__.casefold())


def canonical_record_key(record: EvidenceBackedRecord) -> str:
    prefix = record.institution_id
    if isinstance(record, Course):
        return f"{prefix}:{record.canonical_code}"
    if isinstance(record, Program):
        return f"{prefix}:{record.official_name.casefold()}"
    if isinstance(record, Requirement):
        return f"{prefix}:{record.program_id}:{record.requirement_type}:{record.name.casefold()}"
    if isinstance(record, AdmissionsRule):
        return f"{prefix}:{record.applicant_type}:{record.rule_type}:{record.audience or ''}"
    if isinstance(record, TransferPolicy):
        return ":".join(
            [
                prefix,
                record.policy_type,
                str(record.applicant_type),
                record.sending_institution_type or "",
                record.course_level or "",
            ]
        )
    if isinstance(record, ExamCreditRule):
        return (
            f"{prefix}:{record.exam_type}:{record.exam_name}:{record.score_min}-{record.score_max}"
        )
    return f"{prefix}:{record.id}"
