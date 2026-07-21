"""Deterministic parser for the UW Office of Admissions Bellevue College equivalency guide.

This REPLACED hand-transcription (the now-deleted `curated_equivalencies` module) as
the source of Bellevue College -> UW Seattle equivalency data. Hand-curation already
fabricated two rows once; this module never invents a mapping — every `EquivalencyRecord`
it produces is traced back to an exact row in the source HTML via `evidence_refs`, and any
row whose destination text is conditional, ambiguous, or otherwise structurally
unsupported is routed to `ParseResult.review_rows` instead of being silently published.

The guide is a plain HTML table per subject section:

    <tr>
      <td class="cccourse" scope="row">ACCT&amp; 201, 202 (5, 5) formerly ACCTG 210, 220</td>
      <td class="uwequiv">ACCTG 215 (5), B A 2XX (5) if both courses taken; otherwise, B A 2XX</td>
      <td class="uwreqs"></td>
      <td class="effdate">SUM Qtr. 2008</td>
    </tr>

- `<tr class="obsRow">` rows are historical/superseded and are skipped.
- `<th class="cccourse">` marks a header row (column titles) and is skipped.
- A row whose `uwequiv` cell is empty, or whose `cccourse` text says "see ... combined
  entry", is a cross-reference into another row's entry and is skipped.
- Everything else is either a confident mapping (`records`) or a `ReviewRow` when the
  destination text is conditional (`" if "`, `"otherwise"`, `";"`) or names more than one
  concrete destination.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from selectolax.parser import HTMLParser, Node

from academic_ingest.transfer.models import EquivalencyRecord

_RETRIEVED_DATE = "2026-07-21"

_FORMERLY_RE = re.compile(r"\bformerly\b", re.IGNORECASE)
_BARE_NUMBER_RE = re.compile(r"^[0-9]+[A-Za-z]*$")
_FIRST_CREDITS_RE = re.compile(r"\((\d+(?:\.\d+)?)\)")
_PAREN_NOTE_RE = re.compile(r"\([^()]*\)")
_BRACKET_NOTE_RE = re.compile(r"\[[^\[\]]*\]")
_CONDITIONAL_MARKERS = (" if ", "otherwise", ";")


@dataclass(frozen=True)
class ReviewRow:
    """A guide row that could not be turned into a confident `EquivalencyRecord`.

    Carries the cleaned source/destination cell text verbatim (never a rewritten or
    guessed value) plus the reason it was held back, so a human reviewer can resolve it
    from the same evidence the parser saw.
    """

    reason: str
    source_cell: str
    destination_cell: str
    effective_date: str | None
    evidence_ref: str


@dataclass
class ParseResult:
    """The outcome of parsing the Bellevue equivalency guide."""

    records: list[EquivalencyRecord] = field(default_factory=list)
    review_rows: list[ReviewRow] = field(default_factory=list)
    skipped: dict[str, int] = field(default_factory=dict)


def _increment(skipped: dict[str, int], reason: str) -> None:
    skipped[reason] = skipped.get(reason, 0) + 1


def _clean_cell(node: Node | None) -> str:
    """Extract a table cell's text: entities decoded, leading marker glyphs stripped,
    whitespace collapsed."""
    if node is None:
        return ""
    text = node.text(separator=" ", strip=True)
    index = 0
    while index < len(text) and ord(text[index]) > 127:
        index += 1
    text = text[index:]
    return " ".join(text.split())


def _parse_source_codes(cell_text: str) -> list[str]:
    """Parse the `cccourse` cell into concrete source course codes.

    The course-code list always precedes the first parenthetical (the credits count,
    e.g. `"(5, 5)"` or `"(2, max. 6)"` — note credits themselves can contain a comma, so
    this cell is NOT split on every comma) and any `formerly ...` / `same as ...`
    trailing clause naming historical or cross-listed codes, so it is enough to cut the
    cell at the first `"("` (falling back to a `"formerly"` cut when there is no paren
    at all). `"ACCT& 201, 202 (5, 5)"` -> `["ACCT& 201", "ACCT& 202"]`.
    """
    text = cell_text
    paren_index = text.find("(")
    if paren_index != -1:
        text = text[:paren_index]
    text = _FORMERLY_RE.split(text, maxsplit=1)[0].strip()

    codes: list[str] = []
    last_subject: str | None = None
    for raw_token in text.split(","):
        token = raw_token.strip()
        if not token:
            continue
        if _BARE_NUMBER_RE.fullmatch(token):
            if last_subject is None:
                continue
            codes.append(f"{last_subject} {token}")
            continue
        parts = token.split()
        if len(parts) < 2:
            continue
        number = parts[-1]
        subject = " ".join(parts[:-1])
        last_subject = subject
        codes.append(f"{subject} {number}")
    return codes


def _first_credits(text: str) -> float | None:
    match = _FIRST_CREDITS_RE.search(text)
    if match is None:
        return None
    return float(match.group(1))


def _classify_destination(
    destination_text: str, *, source_code_count: int
) -> tuple[str | None, str | None]:
    """Classify a destination cell.

    Returns `(mapping_type, None)` for a confident, publishable mapping, or
    `(None, review_reason)` when the row must go to `review_rows` instead.
    """
    lower = destination_text.lower()
    if "no credit" in lower:
        return "no_credit", None
    if any(marker in lower for marker in _CONDITIONAL_MARKERS):
        return None, "conditional"

    stripped = _BRACKET_NOTE_RE.sub("", _PAREN_NOTE_RE.sub("", destination_text))
    parts = [part.strip() for part in stripped.split(",") if part.strip()]
    if len(parts) != 1:
        return None, "ambiguous"

    tokens = parts[0].split()
    if len(tokens) < 2:
        return None, "ambiguous"
    number = tokens[-1]
    if "X" in number.upper():
        return "general_elective", None
    if not any(char.isdigit() for char in number):
        return None, "ambiguous"
    if source_code_count >= 2:
        return "sequence_equivalent", None
    return "direct_equivalent", None


def parse_bellevue_equivalencies(html: str, *, source_url: str) -> ParseResult:
    """Deterministically parse the Bellevue College equivalency guide HTML.

    NEVER invents a mapping: every field on every `EquivalencyRecord` traces back to
    text actually present in `html`. Rows with conditional language or more than one
    concrete destination are emitted as `ReviewRow`s, never as records.
    """
    tree = HTMLParser(html)
    result = ParseResult()

    for row in tree.css("tr"):
        if row.css_first("th.cccourse") is not None:
            continue  # header row

        cccourse_node = row.css_first("td.cccourse")
        uwequiv_node = row.css_first("td.uwequiv")
        if cccourse_node is None or uwequiv_node is None:
            continue  # not a data row (e.g. legend/footnote rows)

        source_cell = _clean_cell(cccourse_node)
        destination_cell = _clean_cell(uwequiv_node)
        effdate_node = row.css_first("td.effdate")
        effective_date = _clean_cell(effdate_node) if effdate_node is not None else ""

        if row.attributes.get("class") == "obsRow":
            _increment(result.skipped, "obsolete")
            continue

        source_lower = source_cell.lower()
        if not destination_cell or ("see " in source_lower and "combined entry" in source_lower):
            _increment(result.skipped, "cross_reference")
            continue

        source_codes = _parse_source_codes(source_cell)
        if not source_codes:
            _increment(result.skipped, "unparseable_source")
            continue

        evidence_text = f"{source_cell} => {destination_cell}"
        evidence_ref = f"{source_url} (retrieved {_RETRIEVED_DATE}) :: {evidence_text}"

        mapping_type, review_reason = _classify_destination(
            destination_cell, source_code_count=len(source_codes)
        )
        if review_reason is not None:
            _increment(result.skipped, review_reason)
            result.review_rows.append(
                ReviewRow(
                    reason=review_reason,
                    source_cell=source_cell,
                    destination_cell=destination_cell,
                    effective_date=effective_date or None,
                    evidence_ref=evidence_ref,
                )
            )
            continue

        assert mapping_type is not None  # guaranteed by _classify_destination
        conditions: dict[str, object] = {"effective_date": effective_date} if effective_date else {}
        result.records.append(
            EquivalencyRecord(
                source_course_codes=source_codes,
                mapping_type=mapping_type,
                destination_outcome=destination_cell,
                credits_awarded=_first_credits(destination_cell),
                minimum_grade=None,
                conditions=conditions,
                evidence_refs=[evidence_ref],
            )
        )

    return result
