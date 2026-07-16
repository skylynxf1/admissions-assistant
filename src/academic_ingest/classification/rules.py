from __future__ import annotations

import re
from dataclasses import dataclass

from academic_ingest.models.enums import PolicyFamily, SourceType


@dataclass(frozen=True)
class ClassificationRule:
    path_pattern: re.Pattern[str]
    adapter_name: str
    source_type: SourceType
    policy_family: PolicyFamily


UW_CLASSIFICATION_RULES = (
    ClassificationRule(
        re.compile(r"^/students/crscat/glossary\.html$", re.IGNORECASE),
        "uw.course_glossary",
        SourceType.COURSE_GLOSSARY,
        PolicyFamily.COURSE,
    ),
    ClassificationRule(
        re.compile(r"^/students/crscat/(?:[a-z0-9_-]+\.html)?$", re.IGNORECASE),
        "uw.course_catalog",
        SourceType.COURSE_CATALOG,
        PolicyFamily.COURSE,
    ),
    ClassificationRule(
        re.compile(r"^/students/timeschd(?:/.*)?$", re.IGNORECASE),
        "uw.time_schedule",
        SourceType.COURSE_SCHEDULE,
        PolicyFamily.COURSE_OFFERING,
    ),
    ClassificationRule(
        re.compile(r"^/apply/transfer/equivalency-guide(?:/.*)?$", re.IGNORECASE),
        "uw.equivalency_guide",
        SourceType.EQUIVALENCY_GUIDE,
        PolicyFamily.TRANSFER_POLICY,
    ),
    ClassificationRule(
        re.compile(r"^/academics/majors/?$", re.IGNORECASE),
        "uw.majors_index",
        SourceType.MAJORS_INDEX,
        PolicyFamily.PROGRAM,
    ),
    ClassificationRule(
        re.compile(r"^/majors/[^/]+/?$", re.IGNORECASE),
        "uw.major_detail",
        SourceType.MAJOR_DETAIL,
        PolicyFamily.MAJOR_ADMISSION,
    ),
    ClassificationRule(
        re.compile(r"^/apply/transfer/exams-for-credit/ap/?$", re.IGNORECASE),
        "uw.ap_credit",
        SourceType.EXAM_CREDIT,
        PolicyFamily.EXAM_CREDIT,
    ),
    ClassificationRule(
        re.compile(r"^/apply/transfer/policies/?$", re.IGNORECASE),
        "uw.transfer_policies",
        SourceType.TRANSFER_POLICY,
        PolicyFamily.TRANSFER_POLICY,
    ),
    ClassificationRule(
        re.compile(r"^/apply/(?:transfer|whats-my-application-type)(?:/.*)?$", re.IGNORECASE),
        "uw.transfer_admissions",
        SourceType.ADMISSIONS,
        PolicyFamily.ADMISSIONS,
    ),
)
