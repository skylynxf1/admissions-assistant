from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from urllib.parse import urljoin, urlsplit

from selectolax.parser import HTMLParser, Node

from academic_ingest.adapters.base import AdapterContext, AdapterResult
from academic_ingest.adapters.uw.majors_index import MAJOR_TYPE_LABELS
from academic_ingest.classification.page_classifier import ClassifiedPage
from academic_ingest.discovery.link_discovery import canonicalize_url
from academic_ingest.models.domain import (
    AdmissionsRule,
    EvidenceRecord,
    Program,
    Requirement,
)
from academic_ingest.models.enums import (
    ApplicantType,
    AuthorityTier,
    ConfidenceTier,
    MajorType,
    RequirementType,
    ReviewStatus,
)

COURSE_CODE = re.compile(r"\b(?:[A-Z&]{1,8}(?:\s+[A-Z&]{1,8})*)\s+(?:\d{3}[A-Z]?|[1-9]XX)\b")
TERM_ORDER = ("autumn", "winter", "spring", "summer")


@dataclass(frozen=True)
class OutcomeStatistic:
    label: str
    value: str
    scope: str
    evidence: EvidenceRecord


@dataclass(frozen=True)
class PolicyClaimCandidate:
    field: str
    value: str
    source: str
    evidence: EvidenceRecord


def _clean_text(node: Node) -> str:
    return " ".join(node.text(separator=" ", strip=True).split())


def _selector(node: Node) -> str | None:
    node_id = node.attributes.get("id")
    return f"#{node_id}" if node_id else None


def _major_type(text: str) -> MajorType:
    lowered = text.lower()
    for label, value in MAJOR_TYPE_LABELS.items():
        if label in lowered:
            return value
    return MajorType.UNKNOWN


class MajorDetailAdapter:
    name = "uw.major_detail"
    version = "1.0.0"

    def matches(self, page: ClassifiedPage) -> bool:
        return page.adapter_name == self.name

    def _evidence(
        self,
        context: AdapterContext,
        text: str,
        *,
        selector: str | None = None,
        heading: str | None = None,
        footnote: str | None = None,
    ) -> EvidenceRecord:
        return EvidenceRecord(
            source_snapshot_id=context.source_snapshot_id,
            source_url=context.page.url,
            page_title=context.page.title,
            evidence_text=text,
            css_selector=selector,
            heading_context=heading,
            footnote_context=footnote,
            retrieved_at=context.retrieved_at,
            parser_name=self.name,
            parser_version=self.version,
            authority_tier=AuthorityTier.OFFICIAL_ADMISSIONS,
            confidence_tier=ConfidenceTier.HIGH_CONFIDENCE,
            reviewer_status=ReviewStatus.NOT_REQUIRED,
        )

    def extract(self, context: AdapterContext) -> AdapterResult:
        tree = HTMLParser(context.raw_content)
        result = AdapterResult()
        root = tree.css_first("main")
        if root is None:
            root = tree.root
        if root is None:
            return result
        page_text = _clean_text(root)
        heading = tree.css_first("h1")
        if heading is None:
            return result
        name = _clean_text(heading)
        school_node = tree.css_first(".school, .college, .department")
        school = _clean_text(school_node) if school_node is not None else None
        major_type = _major_type(page_text)
        terms = [
            term
            for term in TERM_ORDER
            if re.search(
                rf"admission[^.]*\b{term}\b[^.]*quarter only",
                page_text,
                flags=re.IGNORECASE,
            )
        ]
        deadline_statements = [
            _clean_text(node)
            for node in tree.css("li, p")
            if "deadline" in _clean_text(node).lower()
        ]
        capacity_match = re.search(
            r"This major is capacity-constrained\.[^.]*\.", page_text, flags=re.IGNORECASE
        )
        page_evidence = self._evidence(
            context,
            page_text,
            selector="main",
            heading=name,
        )
        program = Program(
            institution_id=context.institution_id,
            campus=context.campus,
            evidence=[page_evidence],
            parser_name=self.name,
            parser_version=self.version,
            crawl_job_id=context.crawl_job_id,
            authority_tier=AuthorityTier.OFFICIAL_ADMISSIONS,
            confidence_tier=ConfidenceTier.HIGH_CONFIDENCE,
            review_status=ReviewStatus.NOT_REQUIRED,
            official_name=name,
            college_or_school=school,
            department=school,
            major_type=major_type,
            admission_path=(
                "UW admission plus department-specific process"
                if tree.css_first("#department-admission") is not None
                or "additional application" in page_text.lower()
                else None
            ),
            capacity_status=capacity_match.group(0) if capacity_match else None,
            application_required=(True if "additional application" in page_text.lower() else None),
            application_terms=terms,
            application_deadlines=list(dict.fromkeys(deadline_statements)),
            source_scope="UW Admissions major detail; transfer preparation",
        )
        result.records.append(program)

        notes = tree.css_first("#notes")
        footnote_context = _clean_text(notes) if notes is not None else None
        for section in tree.css("[data-requirement-kind]"):
            kind = (section.attributes.get("data-requirement-kind") or "").lower()
            section_heading = section.css_first("h2, h3, h4")
            requirement_name = (
                _clean_text(section_heading).rstrip(":")
                if section_heading is not None
                else "Major admission requirement"
            )
            section_text = _clean_text(section)
            grade_match = re.search(
                r"minimum grade(?: of)?\s+(\d(?:\.\d+)?)", section_text, re.IGNORECASE
            )
            credit_match = re.search(r"\b(?:at least\s+)?(\d+) credits?\b", section_text, re.I)
            allowed_courses = list(
                dict.fromkeys(
                    " ".join(value.split()) for value in COURSE_CODE.findall(section_text)
                )
            )
            recommended = kind == "recommended"
            evidence = self._evidence(
                context,
                section_text,
                selector=_selector(section),
                heading=requirement_name,
                footnote=footnote_context if not recommended else None,
            )
            result.requirements.append(
                Requirement(
                    institution_id=context.institution_id,
                    campus=context.campus,
                    evidence=[evidence],
                    parser_name=self.name,
                    parser_version=self.version,
                    crawl_job_id=context.crawl_job_id,
                    authority_tier=AuthorityTier.OFFICIAL_ADMISSIONS,
                    confidence_tier=ConfidenceTier.HIGH_CONFIDENCE,
                    review_status=ReviewStatus.NOT_REQUIRED,
                    program_id=program.id,
                    requirement_type=(
                        RequirementType.RECOMMENDED_PREPARATION
                        if recommended
                        else RequirementType.MAJOR_ADMISSION
                    ),
                    name=requirement_name,
                    description=section_text,
                    minimum_credits=(
                        Decimal(credit_match.group(1)) if credit_match is not None else None
                    ),
                    minimum_grade=(
                        Decimal(grade_match.group(1)) if grade_match is not None else None
                    ),
                    allowed_courses=allowed_courses,
                    mandatory=not recommended,
                    recommended=recommended,
                )
            )

        department_section = tree.css_first("#department-admission")
        if department_section is not None:
            for item in department_section.css("li"):
                value = _clean_text(item)
                evidence = self._evidence(
                    context,
                    value,
                    selector=_selector(department_section),
                    heading="Department admission information",
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
                        rule_type="department_admission_condition",
                        value=value,
                        audience=name,
                    )
                )

        for outcome_section in tree.css("[data-outcomes]"):
            outcome_heading = outcome_section.css_first("h2, h3, h4")
            scope = _clean_text(outcome_heading) if outcome_heading is not None else name
            terms_nodes = outcome_section.css("dt")
            values_nodes = outcome_section.css("dd")
            for label_node, value_node in zip(terms_nodes, values_nodes, strict=False):
                label, value = _clean_text(label_node), _clean_text(value_node)
                evidence = self._evidence(
                    context,
                    f"{label}: {value}",
                    selector=_selector(outcome_section),
                    heading=scope,
                )
                result.outcome_statistics.append(
                    OutcomeStatistic(label=label, value=value, scope=scope, evidence=evidence)
                )

        for claim_node in tree.css("[data-claim-field][data-claim-source]"):
            claim_text = _clean_text(claim_node)
            evidence = self._evidence(context, claim_text, selector=_selector(claim_node))
            result.conflict_candidates.append(
                PolicyClaimCandidate(
                    field=claim_node.attributes.get("data-claim-field") or "unknown",
                    value=claim_text,
                    source=claim_node.attributes.get("data-claim-source") or "unknown",
                    evidence=evidence,
                )
            )

        for link in tree.css("a[href]"):
            absolute = canonicalize_url(urljoin(context.page.url, link.attributes["href"]), None)
            host = (urlsplit(absolute).hostname or "").lower()
            if host.endswith(".uw.edu") or host.endswith(".washington.edu"):
                result.discovered_links.append(absolute)
        result.discovered_links = sorted(set(result.discovered_links))
        return result
