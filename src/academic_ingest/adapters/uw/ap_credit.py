from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from selectolax.parser import HTMLParser

from academic_ingest.adapters.base import AdapterContext, AdapterResult
from academic_ingest.adapters.uw.table_evidence import (
    TableRowContext,
    clean_text,
    extract_table_rows,
)
from academic_ingest.classification.page_classifier import ClassifiedPage
from academic_ingest.models.domain import EvidenceRecord, ExamCreditRule, PipelineIssue, ReviewTask
from academic_ingest.models.enums import (
    AuthorityTier,
    ConfidenceTier,
    ReviewStatus,
    Severity,
)

COURSE_CODE = re.compile(
    r"\b([A-Z&]{1,8}(?:\s+[A-Z&]{1,8})*)\s+(\d{3}[A-Z]?)\b",
    re.IGNORECASE,
)
DESIGNATORS = {
    "A&H": "A&H",
    "C": "C",
    "DIV": "DIV",
    "FL": "FL",
    "NSC": "NSc",
    "RSN": "RSN",
    "SSC": "SSc",
}


def _header_index(headers: list[str], *terms: str) -> int | None:
    for index, header in enumerate(headers):
        normalized = header.lower()
        if all(term in normalized for term in terms):
            return index
    return None


def _value(row: TableRowContext, index: int | None) -> str:
    if index is None or index >= len(row.cells):
        return ""
    return row.cells[index].strip()


def _score_band(raw: str) -> tuple[Decimal, Decimal] | None:
    prefix = re.split(r"\bwith\b", raw, maxsplit=1, flags=re.IGNORECASE)[0]
    values = re.findall(r"\d+(?:\.\d+)?", prefix)
    if not values:
        return None
    try:
        scores = [Decimal(value) for value in values]
    except InvalidOperation:
        return None
    if any(score < 1 or score > 5 for score in scores):
        return None
    return min(scores), max(scores)


def _course_codes(raw: str) -> list[str]:
    return list(
        dict.fromkeys(
            f"{' '.join(subject.upper().split())} {number.upper()}"
            for subject, number in COURSE_CODE.findall(raw)
        )
    )


def _credit_values(raw: str) -> list[Decimal | None]:
    return [Decimal(value) for value in re.findall(r"\d+(?:\.\d+)?", raw)]


def _designators(raw: str) -> list[str]:
    values: list[str] = []
    for part in re.split(r"[,/]", raw):
        normalized = part.strip().upper()
        if normalized in DESIGNATORS:
            values.append(DESIGNATORS[normalized])
    return list(dict.fromkeys(values))


class APCreditAdapter:
    name = "uw.ap_credit"
    version = "1.0.0"

    def matches(self, page: ClassifiedPage) -> bool:
        return page.adapter_name == self.name

    def _review(
        self, context: AdapterContext, row: TableRowContext, *, reason: str, question: str
    ) -> ReviewTask:
        return ReviewTask(
            institution_id=context.institution_id,
            source_page_id=context.source_page_id,
            record_type="exam_credit_rule",
            reason=reason,
            severity=Severity.WARNING,
            unresolved_question=f"{question}: {row.evidence_text}",
            recommended_office="UW Office of Admissions",
        )

    def extract(self, context: AdapterContext) -> AdapterResult:
        tree = HTMLParser(context.raw_content)
        result = AdapterResult()
        duplicate_node = next(
            (
                node
                for node in tree.css("p, li")
                if "duplicate or overlapping content" in clean_text(node).lower()
                and "only one" in clean_text(node).lower()
            ),
            None,
        )
        duplicate_rule = clean_text(duplicate_node) if duplicate_node is not None else None

        for row in extract_table_rows(tree):
            name_index = _header_index(row.headers, "name")
            score_index = _header_index(row.headers, "score")
            course_index = _header_index(row.headers, "course")
            credit_index = _header_index(row.headers, "credit", "award")
            requirement_index = _header_index(row.headers, "requirement")
            exam_name = _value(row, name_index)
            raw_score = _value(row, score_index)
            raw_courses = _value(row, course_index)
            raw_credits = _value(row, credit_index)
            if not exam_name or not raw_score:
                result.review_tasks.append(
                    self._review(
                        context,
                        row,
                        reason="exam_row_structure",
                        question="Confirm the exam name and score band",
                    )
                )
                continue
            score_band = _score_band(raw_score)
            if score_band is None:
                result.review_tasks.append(
                    self._review(
                        context,
                        row,
                        reason="exam_score_band",
                        question=f"Confirm the AP score band for {exam_name}",
                    )
                )
                continue
            placement_effect = raw_courses if "placement" in raw_courses.lower() else None
            courses = [] if placement_effect else _course_codes(raw_courses)
            credits = _credit_values(raw_credits)
            if placement_effect and credits == [Decimal(0)]:
                credits = []
            if len(courses) != len(credits):
                result.review_tasks.append(
                    self._review(
                        context,
                        row,
                        reason="exam_award_cardinality",
                        question=(
                            f"Align {len(courses)} awarded courses with "
                            f"{len(credits)} credit values"
                        ),
                    )
                )
                result.warnings.append(
                    PipelineIssue(
                        code="exam_award_cardinality",
                        message=f"Award cardinality is invalid for AP {exam_name}",
                        source_url=context.page.url,
                    )
                )
                continue
            subject_note = row.footnote
            native_rule = (
                subject_note
                if subject_note is not None and "native speaker" in subject_note.lower()
                else None
            )
            notes = [subject_note] if subject_note else []
            evidence = EvidenceRecord(
                source_snapshot_id=context.source_snapshot_id,
                source_url=context.page.url,
                page_title=context.page.title,
                evidence_text=row.evidence_text,
                table_identifier=row.table_identifier,
                row_identifier=row.row_identifier,
                heading_context=row.heading,
                footnote_context=subject_note,
                retrieved_at=context.retrieved_at,
                parser_name=self.name,
                parser_version=self.version,
                authority_tier=AuthorityTier.OFFICIAL_ADMISSIONS,
                confidence_tier=ConfidenceTier.HIGH_CONFIDENCE,
                reviewer_status=ReviewStatus.NOT_REQUIRED,
            )
            result.records.append(
                ExamCreditRule(
                    institution_id=context.institution_id,
                    campus=context.campus,
                    evidence=[evidence],
                    parser_name=self.name,
                    parser_version=self.version,
                    crawl_job_id=context.crawl_job_id,
                    authority_tier=AuthorityTier.OFFICIAL_ADMISSIONS,
                    confidence_tier=ConfidenceTier.HIGH_CONFIDENCE,
                    review_status=ReviewStatus.NOT_REQUIRED,
                    exam_type="AP",
                    exam_name=exam_name,
                    score_min=score_band[0],
                    score_max=score_band[1],
                    awarded_courses=courses,
                    awarded_credit_values=credits,
                    general_education_designators=_designators(_value(row, requirement_index)),
                    placement_effect=placement_effect,
                    duplicate_credit_rule=duplicate_rule,
                    native_speaker_rule=native_rule,
                    major_specific_applicability="unknown",
                    notes=notes,
                )
            )
        return result
