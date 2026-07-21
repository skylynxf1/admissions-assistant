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
    PipelineIssue,
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

# Structural (template-level) markers used by the current admit.washington.edu
# major-detail pages, which no longer emit the `[data-requirement-kind]`
# attributes the old fixture used. These match the WordPress template's own
# heading wording, not any single major's content.
REQUIREMENT_HEADING = re.compile(r"courses?\s+(required|recommended)\s+for\s+admission", re.I)
GRADE_LINE = re.compile(r"^minimum grade(?:\s+of)?\s+(\d(?:\.\d+)?)\s+in each course", re.I)
ONE_OF_PHRASE = re.compile(r"\bone of\b", re.I)
CREDITS_PHRASE = re.compile(r"(\d+)\s+credits?\b", re.I)
OTHER_THAN = re.compile(r"other than\s+" + COURSE_CODE.pattern, re.I)
# Hyphen, en dash (U+2013), em dash (U+2014) — built via chr() to avoid an
# ambiguous-unicode-character lint warning for the literal glyphs.
_DASH_CHARS = "-" + chr(0x2013) + chr(0x2014)
TITLE_AFTER_DASH = re.compile(rf"[{_DASH_CHARS}]\s*(.+)$")


def _next_element(node: Node) -> Node | None:
    """Walk forward past text/comment pseudo-nodes to the next element sibling."""
    current = node.next
    while current is not None and (current.tag is None or current.tag.startswith("-")):
        current = current.next
    return current


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

    def _structural_requirement_name(
        self, text: str, allowed_courses: list[str], minimum_courses: int | None
    ) -> str:
        if minimum_courses == 1 and allowed_courses:
            return "One of the following courses"
        if len(allowed_courses) == 1:
            code = allowed_courses[0]
            idx = text.find(code)
            remainder = text[idx + len(code) :] if idx != -1 else text
            title_match = TITLE_AFTER_DASH.search(remainder)
            if title_match:
                title = title_match.group(1).strip()
                if title:
                    return title[:120]
            return code
        if allowed_courses:
            return "Required courses"
        return text if len(text) <= 80 else text[:77].rstrip() + "..."

    def _extract_structural_requirements(
        self,
        tree: HTMLParser,
        context: AdapterContext,
        program: Program,
        result: AdapterResult,
    ) -> bool:
        """Fallback for the current admit.washington.edu template, which lists
        requirements as `<li>` items under a "Courses REQUIRED/RECOMMENDED for
        admission:" `<h3>` heading instead of `[data-requirement-kind]`
        sections. One `Requirement` is emitted per bullet; a trailing
        "Minimum grade of X in each course." bullet is not itself a
        requirement — its grade is applied back onto the bullets in the same
        list.
        """
        found_any = False
        for heading in tree.css("h2, h3, h4"):
            heading_text = _clean_text(heading)
            heading_match = REQUIREMENT_HEADING.search(heading_text)
            if heading_match is None:
                continue
            recommended = heading_match.group(1).lower() == "recommended"
            list_node = _next_element(heading)
            if list_node is None or list_node.tag not in ("ul", "ol"):
                continue
            group: list[Requirement] = []
            list_id = list_node.attributes.get("id")
            list_base_selector = f"#{list_id}" if list_id else list_node.tag
            for li_index, li in enumerate(list_node.css("li"), start=1):
                text = _clean_text(li)
                if not text:
                    continue
                grade_match = GRADE_LINE.match(text)
                if grade_match is not None:
                    grade_value = Decimal(grade_match.group(1))
                    for requirement in group:
                        requirement.minimum_grade = grade_value
                    continue
                excluded_courses = {
                    code
                    for excluded_match in OTHER_THAN.finditer(text)
                    for code in COURSE_CODE.findall(excluded_match.group(0))
                }
                allowed_courses = [
                    code
                    for code in dict.fromkeys(
                        " ".join(value.split()) for value in COURSE_CODE.findall(text)
                    )
                    if code not in excluded_courses
                ]
                minimum_courses = (
                    1
                    if allowed_courses
                    and (
                        ONE_OF_PHRASE.search(text) is not None
                        or (len(allowed_courses) >= 2 and re.search(r"\bor\b", text, re.I))
                    )
                    else None
                )
                credit_match = CREDITS_PHRASE.search(text)
                name = self._structural_requirement_name(text, allowed_courses, minimum_courses)
                evidence = self._evidence(
                    context,
                    text,
                    selector=f"{list_base_selector} > li:nth-child({li_index})",
                    heading=heading_text,
                )
                requirement = Requirement(
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
                    name=name,
                    description=text,
                    minimum_credits=(
                        Decimal(credit_match.group(1)) if credit_match is not None else None
                    ),
                    minimum_courses=minimum_courses,
                    allowed_courses=allowed_courses,
                    mandatory=not recommended,
                    recommended=recommended,
                )
                group.append(requirement)
                found_any = True
            result.requirements.extend(group)
        return found_any

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
        requirement_kind_sections = tree.css("[data-requirement-kind]")
        if requirement_kind_sections:
            for section in requirement_kind_sections:
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
        else:
            found_any = self._extract_structural_requirements(tree, context, program, result)
            if not found_any:
                result.warnings.append(
                    PipelineIssue(
                        code="major_detail_requirements_unrecognized",
                        message=(
                            "No recognized admission-requirement structure "
                            "(neither [data-requirement-kind] sections nor a "
                            "'Courses REQUIRED/RECOMMENDED for admission' heading "
                            "followed by a list) was found on this major detail page."
                        ),
                        source_url=context.page.url,
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
