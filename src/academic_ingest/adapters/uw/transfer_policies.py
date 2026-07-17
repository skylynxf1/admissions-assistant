from __future__ import annotations

import re
from decimal import Decimal

from selectolax.parser import HTMLParser, Node

from academic_ingest.adapters.base import AdapterContext, AdapterResult
from academic_ingest.adapters.uw.table_evidence import (
    TableRowContext,
    clean_text,
    extract_table_rows,
)
from academic_ingest.classification.page_classifier import ClassifiedPage
from academic_ingest.models.domain import EvidenceRecord, PipelineIssue, TransferPolicy
from academic_ingest.models.enums import (
    ApplicantType,
    AuthorityTier,
    ConfidenceTier,
    MappingOutcome,
    ReviewStatus,
)

EXPLICIT_NO_CREDIT = re.compile(
    r"(?:receive(?:s)? no credit|no credit (?:is )?awarded|credit is not (?:granted|awarded))",
    re.IGNORECASE,
)


class TransferPolicyAdapter:
    name = "uw.transfer_policies"
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

    def _table_policy(self, context: AdapterContext, row: TableRowContext) -> TransferPolicy:
        first_cell = row.cells[0].lower() if row.cells else ""
        inferred_type = "transfer_table_rule"
        inferred_course_level: str | None = None
        if "lower-division" in first_cell:
            inferred_type = "lower_division_limit"
            inferred_course_level = "lower_division"
        elif "total transfer" in first_cell:
            inferred_type = "total_transfer_limit"
        elif first_cell in {"first-year", "sophomore", "junior", "senior"}:
            inferred_type = f"class_standing_{first_cell.replace('-', '_')}"
        policy_type = row.row_attributes.get("data-policy-type") or inferred_type
        credit_match = re.search(r"\d+(?:\.\d+)?", row.cells[1]) if len(row.cells) > 1 else None
        credit_limit = Decimal(credit_match.group(0)) if credit_match else None
        conditions = {header: value for header, value in zip(row.headers, row.cells, strict=False)}
        evidence = self._evidence(
            context,
            row.evidence_text,
            heading=row.heading,
            row=row,
        )
        return TransferPolicy(
            institution_id=context.institution_id,
            campus=context.campus,
            evidence=[evidence],
            parser_name=self.name,
            parser_version=self.version,
            crawl_job_id=context.crawl_job_id,
            authority_tier=AuthorityTier.OFFICIAL_ADMISSIONS,
            confidence_tier=ConfidenceTier.HIGH_CONFIDENCE,
            review_status=ReviewStatus.NOT_REQUIRED,
            policy_type=policy_type,
            applicant_type=ApplicantType.TRANSFER,
            credit_limit=credit_limit,
            course_level=row.row_attributes.get("data-course-level") or inferred_course_level,
            degree_applicability=row.cells[2] if len(row.cells) > 2 else None,
            conditions=conditions,
        )

    def _semantic_policy(
        self,
        context: AdapterContext,
        node: Node,
        policy_type: str,
        *,
        explicit_no_credit: bool = False,
        heading_override: str | None = None,
    ) -> TransferPolicy | None:
        text = clean_text(node)
        heading_node = node.css_first("h2, h3, h4")
        heading = clean_text(heading_node) if heading_node is not None else heading_override
        claimed_outcome = node.attributes.get("data-mapping-outcome")
        conditions: dict[str, object] = {}
        if explicit_no_credit or claimed_outcome == MappingOutcome.EXPLICIT_NO_CREDIT.value:
            if not EXPLICIT_NO_CREDIT.search(text):
                return None
            conditions["mapping_outcome"] = MappingOutcome.EXPLICIT_NO_CREDIT.value
        if "not an admission agreement" in text.lower():
            conditions["admission_agreement"] = False
        conversion = re.search(r"multiply by\s+(\d+(?:\.\d+)?)", text, re.IGNORECASE)
        if conversion:
            conditions["conversion_factor"] = conversion.group(1)
        standing = "Junior standing upon admission" if "junior standing" in text.lower() else None
        credit_limit_match = re.search(
            r"(?:maximum of|up to|no more than)\s+(\d+)\s+(?:quarter\s+)?credits",
            text,
            re.IGNORECASE,
        )
        node_id = node.attributes.get("id")
        evidence = self._evidence(
            context,
            text,
            heading=heading,
            selector=f"#{node_id}" if node_id else None,
        )
        return TransferPolicy(
            institution_id=context.institution_id,
            campus=context.campus,
            evidence=[evidence],
            parser_name=self.name,
            parser_version=self.version,
            crawl_job_id=context.crawl_job_id,
            authority_tier=AuthorityTier.OFFICIAL_ADMISSIONS,
            confidence_tier=ConfidenceTier.HIGH_CONFIDENCE,
            review_status=ReviewStatus.NOT_REQUIRED,
            policy_type=policy_type,
            applicant_type=ApplicantType.TRANSFER,
            credit_limit=(
                Decimal(credit_limit_match.group(1)) if credit_limit_match is not None else None
            ),
            class_standing_effect=standing,
            degree_applicability=text,
            conditions=conditions,
        )

    def extract(self, context: AdapterContext) -> AdapterResult:
        tree = HTMLParser(context.raw_content)
        result = AdapterResult()
        for row in extract_table_rows(tree):
            result.records.append(self._table_policy(context, row))

        for node in tree.css("[data-policy-type]"):
            if node.tag == "tr":
                continue
            policy_type = node.attributes.get("data-policy-type") or "transfer_policy"
            policy = self._semantic_policy(context, node, policy_type)
            if policy is None:
                result.warnings.append(
                    PipelineIssue(
                        code="unsupported_no_credit_claim",
                        message="A no-credit marker lacked explicit no-credit source language",
                        source_url=context.page.url,
                    )
                )
                continue
            result.records.append(policy)

        semantic_sections = {
            "direct transfer agreement": "direct_transfer_agreement",
            "quarter vs. semester credits": "semester_to_quarter_conversion",
            "senior residency requirement": "senior_residency_requirement",
            "restricted transfer credit": "restricted_transfer_credit",
            "extension credit from other schools": "extension_credit_limit",
        }
        existing_evidence = {
            item.evidence[0].evidence_text for item in result.records if item.evidence
        }
        for section in tree.css("section"):
            heading_node = section.css_first("h2, h3, h4")
            if heading_node is None:
                continue
            heading = clean_text(heading_node)
            normalized_heading = heading.lower()
            if normalized_heading == "courses receiving no credit":
                for item in section.css("li"):
                    policy = self._semantic_policy(
                        context,
                        item,
                        "no_credit_category",
                        explicit_no_credit=True,
                        heading_override=heading,
                    )
                    if (
                        policy is not None
                        and policy.evidence[0].evidence_text not in existing_evidence
                    ):
                        result.records.append(policy)
                        existing_evidence.add(policy.evidence[0].evidence_text)
                continue
            semantic_policy_type = semantic_sections.get(normalized_heading)
            if normalized_heading.startswith("direct transfer agreement"):
                semantic_policy_type = "direct_transfer_agreement"
            if semantic_policy_type is None:
                continue
            policy = self._semantic_policy(context, section, semantic_policy_type)
            if policy is not None and policy.evidence[0].evidence_text not in existing_evidence:
                result.records.append(policy)
                existing_evidence.add(policy.evidence[0].evidence_text)
        return result
