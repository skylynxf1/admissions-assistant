from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit

from selectolax.parser import HTMLParser, Node

from academic_ingest.adapters.base import AdapterContext, AdapterResult
from academic_ingest.classification.page_classifier import ClassifiedPage
from academic_ingest.discovery.link_discovery import discover_links
from academic_ingest.models.domain import Course, EvidenceRecord, PipelineIssue, ReviewTask
from academic_ingest.models.enums import (
    AuthorityTier,
    ConfidenceTier,
    CreditType,
    ReviewStatus,
    Severity,
)

COURSE_HEADING = re.compile(
    r"^(?P<subject>[A-Z][A-Z&]*(?:\s+[A-Z][A-Z&]*)*)\s+"
    r"(?P<number>(?:\d{3}[A-Z]?|[1-9]XX))\s+"
    r"(?P<title>.+?)\s+\((?P<credits>[^)]+)\)(?:\s+(?P<designators>.*))?$"
)
COURSE_CODE = re.compile(r"\b(?:[A-Z&]{1,8}(?:\s+[A-Z&]{1,8})*)\s+(?:\d{3}[A-Z]?|[1-9]XX)\b")
KNOWN_DESIGNATORS = {
    "A&H": "A&H",
    "C": "C",
    "DIV": "DIV",
    "NSC": "NSc",
    "QSR": "QSR",
    "RSN": "RSN",
    "SSC": "SSc",
    "W": "W",
}
SEMANTIC_MARKERS = (
    "Course equivalent to:",
    "Course overlaps with:",
    "Prerequisite:",
    "Recommended:",
    "Offered:",
    "Open only",
    "Cannot be taken",
    "Must be taken",
    "Credit/no-credit only",
)


@dataclass(frozen=True)
class CourseCandidate:
    subject: str
    number: str
    title: str
    credits_min: Decimal | None
    credits_max: Decimal | None
    designators: list[str]
    body_text: str
    evidence_text: str
    css_selector: str | None

    @property
    def canonical_code(self) -> str:
        return f"{self.subject} {self.number}"


def _clean_lines(node: Node) -> list[str]:
    return [
        " ".join(line.split())
        for line in node.text(separator="\n", strip=True).splitlines()
        if line.strip()
    ]


def _parse_credits(raw: str) -> tuple[Decimal | None, Decimal | None]:
    primary = raw.split(",", 1)[0].strip()
    if primary == "*":
        return None, None
    values = re.findall(r"\d+(?:\.\d+)?", primary)
    if not values:
        return None, None
    try:
        decimals = [Decimal(value) for value in values]
    except InvalidOperation:
        return None, None
    return min(decimals), max(decimals)


def _parse_designators(raw: str | None) -> list[str]:
    if not raw:
        return []
    result: list[str] = []
    for value in re.split(r"[,;/]", raw):
        normalized = " ".join(value.split()).upper()
        if normalized in KNOWN_DESIGNATORS:
            result.append(KNOWN_DESIGNATORS[normalized])
    return list(dict.fromkeys(result))


def _selector(node: Node) -> str | None:
    node_id = node.attributes.get("id")
    if node_id:
        return f"#{node_id}"
    anchor = node.css_first("a[id], a[name]")
    if anchor is None:
        return None
    anchor_id = anchor.attributes.get("id") or anchor.attributes.get("name")
    return f"#{anchor_id}" if anchor_id else None


def _clause(body: str, label: str) -> str | None:
    following_markers = "|".join(
        re.escape(marker) for marker in SEMANTIC_MARKERS if marker != label
    )
    match = re.search(
        rf"{re.escape(label)}\s*(.+?)(?=(?:{following_markers})|$)",
        body,
        flags=re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def _referenced_courses(value: str | None) -> list[str]:
    if not value:
        return []
    return list(dict.fromkeys(" ".join(match.split()) for match in COURSE_CODE.findall(value)))


def _description(body: str) -> str:
    positions = [body.lower().find(marker.lower()) for marker in SEMANTIC_MARKERS]
    starts = [position for position in positions if position >= 0]
    return body[: min(starts)].strip() if starts else body.strip()


def _restrictions(body: str) -> list[str]:
    restrictions = re.findall(
        r"(?:Open only|Cannot be taken|Must be taken|Credit/no-credit only)[^.]*\.?",
        body,
        flags=re.IGNORECASE,
    )
    return [restriction.strip() for restriction in restrictions]


class CourseCatalogAdapter:
    name = "uw.course_catalog"
    version = "1.0.0"

    def matches(self, page: ClassifiedPage) -> bool:
        return page.adapter_name == self.name

    def extract_course_blocks(self, html: bytes) -> list[CourseCandidate]:
        tree = HTMLParser(html)
        candidates: list[CourseCandidate] = []
        for paragraph in tree.css("p"):
            heading_node = paragraph.css_first("b, strong")
            lines = _clean_lines(paragraph)
            if not lines:
                continue
            heading = (
                " ".join(heading_node.text(separator=" ", strip=True).split())
                if heading_node is not None
                else lines[0]
            )
            match = COURSE_HEADING.fullmatch(heading)
            if match is None:
                continue
            evidence_text = "\n".join(lines)
            body_lines = [line for line in lines if line != heading]
            body_text = " ".join(
                line for line in body_lines if not line.startswith("View course details in MyPlan:")
            )
            credits_min, credits_max = _parse_credits(match.group("credits"))
            candidates.append(
                CourseCandidate(
                    subject=" ".join(match.group("subject").split()),
                    number=match.group("number"),
                    title=match.group("title").strip(),
                    credits_min=credits_min,
                    credits_max=credits_max,
                    designators=_parse_designators(match.group("designators")),
                    body_text=body_text,
                    evidence_text=evidence_text,
                    css_selector=_selector(paragraph),
                )
            )
        return candidates

    def extract(self, context: AdapterContext) -> AdapterResult:
        result = AdapterResult()
        candidates = self.extract_course_blocks(context.raw_content)
        if not candidates:
            links = discover_links(
                context.page.url,
                context.raw_content,
                allowed_domains={"www.washington.edu"},
            )
            result.discovered_links = [
                link
                for link in links
                if "/students/crscat/" in link
                and link.lower().endswith(".html")
                and urlsplit(link).path.rsplit("/", 1)[-1].lower() != "glossary.html"
            ]
            return result

        for candidate in candidates:
            if (
                context.selected_course_codes is not None
                and candidate.canonical_code not in context.selected_course_codes
            ):
                continue
            if candidate.credits_min is None or candidate.credits_max is None:
                result.review_tasks.append(
                    ReviewTask(
                        institution_id=context.institution_id,
                        source_page_id=context.source_page_id,
                        record_type="course",
                        reason="unparseable_credit",
                        severity=Severity.WARNING,
                        unresolved_question=(
                            f"Confirm the credit value for {candidate.canonical_code}: "
                            f"{candidate.evidence_text}"
                        ),
                        recommended_office="UW Office of the University Registrar",
                    )
                )
                result.warnings.append(
                    PipelineIssue(
                        code="course_credit_unresolved",
                        message=f"Credit value is unresolved for {candidate.canonical_code}",
                        source_url=context.page.url,
                    )
                )
                continue
            evidence = EvidenceRecord(
                source_snapshot_id=context.source_snapshot_id,
                source_url=context.page.url,
                page_title=context.page.title,
                evidence_text=candidate.evidence_text,
                css_selector=candidate.css_selector,
                retrieved_at=context.retrieved_at,
                parser_name=self.name,
                parser_version=self.version,
                authority_tier=AuthorityTier.OFFICIAL_CATALOG,
                confidence_tier=ConfidenceTier.HIGH_CONFIDENCE,
                reviewer_status=ReviewStatus.NOT_REQUIRED,
            )
            prerequisite = _clause(candidate.body_text, "Prerequisite:")
            offering_note = _clause(candidate.body_text, "Offered:")
            result.records.append(
                Course(
                    institution_id=context.institution_id,
                    campus=context.campus,
                    evidence=[evidence],
                    parser_name=self.name,
                    parser_version=self.version,
                    crawl_job_id=context.crawl_job_id,
                    authority_tier=AuthorityTier.OFFICIAL_CATALOG,
                    confidence_tier=ConfidenceTier.HIGH_CONFIDENCE,
                    review_status=ReviewStatus.NOT_REQUIRED,
                    subject=candidate.subject,
                    number=candidate.number,
                    title=candidate.title,
                    description=_description(candidate.body_text),
                    credits_min=candidate.credits_min,
                    credits_max=candidate.credits_max,
                    credit_type=CreditType.QUARTER,
                    prerequisite_text=prerequisite,
                    restrictions=_restrictions(candidate.body_text),
                    equivalent_courses=_referenced_courses(
                        _clause(candidate.body_text, "Course equivalent to:")
                    ),
                    overlapping_courses=_referenced_courses(
                        _clause(candidate.body_text, "Course overlaps with:")
                    ),
                    general_education_designators=candidate.designators,
                    historical_offering_notes=[offering_note] if offering_note else [],
                )
            )
        return result
