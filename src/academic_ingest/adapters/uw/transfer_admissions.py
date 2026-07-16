from __future__ import annotations

from selectolax.parser import HTMLParser, Node

from academic_ingest.adapters.base import AdapterContext, AdapterResult
from academic_ingest.adapters.uw.table_evidence import (
    TableRowContext,
    clean_text,
    extract_table_rows,
)
from academic_ingest.classification.page_classifier import ClassifiedPage
from academic_ingest.models.domain import AdmissionsRule, EvidenceRecord
from academic_ingest.models.enums import (
    ApplicantType,
    AuthorityTier,
    ConfidenceTier,
    ReviewStatus,
)

APPLICANT_TYPES = {
    "first-year": ApplicantType.FIRST_YEAR,
    "transfer": ApplicantType.TRANSFER,
    "postbaccalaureate": ApplicantType.POSTBACCALAUREATE,
    "running-start": ApplicantType.RUNNING_START,
    "international": ApplicantType.INTERNATIONAL,
}


class TransferAdmissionsAdapter:
    name = "uw.transfer_admissions"
    version = "1.0.0"

    def matches(self, page: ClassifiedPage) -> bool:
        return page.adapter_name == self.name

    def _evidence(
        self,
        context: AdapterContext,
        text: str,
        *,
        heading: str | None,
        selector: str | None = None,
        row: TableRowContext | None = None,
    ) -> EvidenceRecord:
        return EvidenceRecord(
            source_snapshot_id=context.source_snapshot_id,
            source_url=context.page.url,
            page_title=context.page.title,
            evidence_text=text,
            css_selector=selector,
            table_identifier=row.table_identifier if row else None,
            row_identifier=row.row_identifier if row else None,
            heading_context=heading,
            footnote_context=row.footnote if row else None,
            retrieved_at=context.retrieved_at,
            parser_name=self.name,
            parser_version=self.version,
            authority_tier=AuthorityTier.OFFICIAL_ADMISSIONS,
            confidence_tier=ConfidenceTier.HIGH_CONFIDENCE,
            reviewer_status=ReviewStatus.NOT_REQUIRED,
        )

    def _definition_rule(
        self, context: AdapterContext, section: Node, applicant_type: ApplicantType
    ) -> AdmissionsRule:
        text = clean_text(section)
        heading_node = section.css_first("h2, h3")
        heading = clean_text(heading_node) if heading_node is not None else "Applicant definition"
        section_id = section.attributes.get("id")
        evidence = self._evidence(
            context,
            text,
            heading=heading,
            selector=f"#{section_id}" if section_id else None,
        )
        return AdmissionsRule(
            institution_id=context.institution_id,
            campus=context.campus,
            evidence=[evidence],
            parser_name=self.name,
            parser_version=self.version,
            crawl_job_id=context.crawl_job_id,
            authority_tier=AuthorityTier.OFFICIAL_ADMISSIONS,
            confidence_tier=ConfidenceTier.HIGH_CONFIDENCE,
            review_status=ReviewStatus.NOT_REQUIRED,
            applicant_type=applicant_type,
            rule_type="applicant_definition",
            value=text,
            audience=heading,
            conditions={"all_statements_required": "all" in text.lower()},
        )

    def extract(self, context: AdapterContext) -> AdapterResult:
        tree = HTMLParser(context.raw_content)
        result = AdapterResult()
        definition_sections = tree.css("[data-applicant-type]")
        if not definition_sections:
            definition_sections = [
                section
                for section in tree.css("section")
                if "applicant definition" in clean_text(section).lower()
            ]
        for section in definition_sections:
            raw_type = (section.attributes.get("data-applicant-type") or "").lower()
            section_text = clean_text(section).lower()
            applicant_type = APPLICANT_TYPES.get(raw_type)
            if applicant_type is None:
                applicant_type = next(
                    (
                        value
                        for label, value in APPLICANT_TYPES.items()
                        if label.replace("-", " ") in section_text
                    ),
                    ApplicantType.UNKNOWN,
                )
            result.records.append(self._definition_rule(context, section, applicant_type))

        for row in extract_table_rows(tree):
            heading = row.heading or "Admissions table"
            if "date" not in heading.lower() and "deadline" not in heading.lower():
                continue
            values = {
                header.strip().lower().replace(" ", "_"): value
                for header, value in zip(row.headers, row.cells, strict=False)
            }
            timing = row.cells[0] if row.cells else None
            evidence = self._evidence(
                context,
                row.evidence_text,
                heading=heading,
                row=row,
            )
            result.records.append(
                AdmissionsRule(
                    institution_id=context.institution_id,
                    campus=context.campus,
                    evidence=[evidence],
                    parser_name=self.name,
                    parser_version=self.version,
                    crawl_job_id=context.crawl_job_id,
                    authority_tier=AuthorityTier.OFFICIAL_ADMISSIONS,
                    confidence_tier=ConfidenceTier.HIGH_CONFIDENCE,
                    review_status=ReviewStatus.NOT_REQUIRED,
                    applicant_type=ApplicantType.TRANSFER,
                    rule_type="application_deadline",
                    value=" | ".join(row.cells),
                    timing=timing,
                    audience="Transfer applicants",
                    conditions=values,
                )
            )
        return result
