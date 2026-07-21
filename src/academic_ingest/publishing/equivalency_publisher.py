"""Publish curated Bellevue College -> UW Seattle equivalencies into Supabase.

Moves the 15 CITED `EquivalencyRecord`s in
`academic_ingest.transfer.curated_equivalencies` (currently served from memory by the
resolver) into `equivalency.course_equivalencies` + `equivalency.equivalency_components`,
resolving each free-text `destination_outcome` to a real `catalog.courses` foreign key
where possible.

Two clearly separated layers, mirroring `supabase_publisher.py`:

1. PURE (`parse_course_code`, `parse_destination`, `build_equivalency_intents`) —
   deterministic, offline-testable, no client/I-O.
2. EXECUTOR (`publish_equivalencies`) — thin I/O against a live Supabase client. Not
   unit-tested against a real network; the `supabase` package is imported lazily
   (inside `EquivalencyPublisher.from_env`) so offline pytest runs never need a live
   client. `NAMESPACE` and `_filter_eq_or_null` are reused directly from
   `supabase_publisher` (also stdlib-only at import time) rather than duplicated.

THE CRITICAL RULE: never invent a course. Bellevue source courses do not exist yet in
`catalog.courses`, so minimal rows are created for them (deterministic uuid5 id,
`campus="Main"`). UW destination courses, in contrast, are looked up only — if a parsed
destination (e.g. "CSE 100") does not exist in the live UW catalog, it is recorded as a
`component_role='category'` component instead of a fabricated course row. Non-course
destinations ("No credit") and wildcard outcomes ("1XX", "ART 1XX") never even attempt
resolution: `parse_destination` returns `None` for them up front.

Idempotency:
  - Bellevue source courses: select-then-update-or-insert by the natural key
    `(institution_id, campus, subject, number)`, same pattern (and same rationale —
    never reassign an existing row's `id`) as `supabase_publisher._upsert_courses`.
  - `course_equivalencies`: the row's natural key (source codes + destination outcome
    text) IS the deterministic uuid5 `id` on its `EquivalencyIntent`, so a plain
    select-by-id then update-or-insert is safe here without a separate natural-key
    lookup — the id used to look the row up is exactly the id used to write it, so an
    existing row's id is never reassigned across runs.
  - `equivalency_components`: replaced idempotently per equivalency (delete existing
    rows for `equivalency_id`, then insert fresh ones) so re-running never duplicates
    or accumulates stale components.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any

from academic_ingest.publishing.supabase_publisher import NAMESPACE, _filter_eq_or_null

if TYPE_CHECKING:
    from academic_ingest.transfer.models import EquivalencyRecord

_BELLEVUE_CAMPUS = "Main"


# ---------------------------------------------------------------------------
# PURE (offline-testable)
# ---------------------------------------------------------------------------


def parse_course_code(code: str) -> tuple[str, str] | None:
    """Split a course code into `(subject, number)`.

    The NUMBER is the last whitespace-separated token that starts with a digit;
    everything before it is the subject. Returns `None` if no token starts with a
    digit (e.g. "No credit").

    Examples: "MATH& 151" -> ("MATH&", "151"); "ART H 201" -> ("ART H", "201");
    "NURS 100X" -> ("NURS", "100X").
    """
    tokens = code.split()
    number_index = None
    for index, token in enumerate(tokens):
        if token[:1].isdigit():
            number_index = index
    if number_index is None:
        return None
    number = tokens[number_index]
    subject = " ".join(tokens[:number_index])
    return subject, number


_LEADING_DESTINATION_CODE_RE = re.compile(r"^([A-Z][A-Z&]*(?:\s+[A-Z][A-Z&]*)*)\s+(\d\S*)")
_SOURCE_CLAUSE_RE = re.compile(r"\bfor\s+(?:either\s+)?")
_OR_ALTERNATIVE_RE = re.compile(r"\bor\s+[A-Z][A-Z&]*(?:\s+[A-Z][A-Z&]*)*\s+\d\S*")


def parse_destination(outcome: str) -> tuple[str, str] | None:
    """Resolve a free-text destination outcome to `(subject, number)`, or `None`.

    Unlike `parse_course_code` (used for SOURCE codes, which are bare "SUBJECT
    NUMBER" strings), destination cells routinely carry trailing prose — e.g.
    "FRENCH 101 (5) for either FRCH& 121 or FRCH 131". Taking the last digit-led
    token (as `parse_course_code` does) grabs garbage from that prose, so this
    parses the course code from the START of the string instead:

    1. Strips a leading "UW " prefix if present.
    2. Matches a leading SUBJECT (one or more uppercase/"&" tokens) immediately
       followed by a NUMBER token starting with a digit.
    3. Returns `None` for wildcard numbers containing "X" ("1XX", "UW 1XX (LC)",
       "ART 1XX") — those are categories, not specific courses.
    4. Returns `None` when the remaining text genuinely offers ALTERNATIVE
       destination courses (e.g. "ANTH 203 (5) or LING 203 (5)"), detected as an
       " or SUBJECT NUMBER" pattern that is not part of a "for either ... or ..."
       clause describing SOURCE options (e.g. the FRENCH example above, where the
       leading destination code stands and the "or" belongs to the source list).
    5. Returns `None` if no leading code matches at all (e.g. "No credit").
    """
    text = outcome[3:] if outcome.startswith("UW ") else outcome
    match = _LEADING_DESTINATION_CODE_RE.match(text)
    if match is None:
        return None
    subject, number = match.group(1), match.group(2)
    if "X" in number.upper():
        return None

    remainder = text[match.end() :]
    source_clause = _SOURCE_CLAUSE_RE.search(remainder)
    for or_match in _OR_ALTERNATIVE_RE.finditer(remainder):
        if source_clause is not None and or_match.start() > source_clause.start():
            # The "or" belongs to a "for either <source> or <source>" clause
            # describing SOURCE alternatives, not destination ones.
            continue
        return None
    return subject, number


@dataclass
class EquivalencyIntent:
    """A single equivalency record, parsed and given a deterministic id."""

    id: str
    source_courses: list[tuple[str, str]]
    destination: tuple[str, str] | None
    mapping_type: str
    credits_awarded: float | None
    minimum_grade: str | None
    conditions: dict[str, Any]
    evidence_refs: list[str]
    destination_outcome: str


def build_equivalency_intents(records: list[EquivalencyRecord]) -> list[EquivalencyIntent]:
    """Pure transform: `EquivalencyRecord`s -> `EquivalencyIntent`s.

    Source codes that fail to parse are skipped defensively (never invents a course
    for an unparseable code); in practice every curated Bellevue source code parses.
    """
    intents = []
    for record in records:
        key = f"{'+'.join(record.source_course_codes)}=>{record.destination_outcome}"
        intent_id = str(uuid.uuid5(NAMESPACE, key))
        source_courses = [
            parsed
            for code in record.source_course_codes
            if (parsed := parse_course_code(code)) is not None
        ]
        intents.append(
            EquivalencyIntent(
                id=intent_id,
                source_courses=source_courses,
                destination=parse_destination(record.destination_outcome),
                mapping_type=record.mapping_type,
                credits_awarded=record.credits_awarded,
                minimum_grade=record.minimum_grade,
                conditions=dict(record.conditions),
                evidence_refs=list(record.evidence_refs),
                destination_outcome=record.destination_outcome,
            )
        )
    return intents


# ---------------------------------------------------------------------------
# EXECUTOR (thin I/O; exercised live against a real Supabase project)
# ---------------------------------------------------------------------------


@dataclass
class PublishReport:
    """Counts returned by the live executor after a `publish_equivalencies` run."""

    equivalencies_upserted: int = 0
    source_courses_created: int = 0
    source_course_versions_created: int = 0
    destinations_resolved: int = 0
    destinations_as_category: int = 0
    unresolved_destinations: list[str] = field(default_factory=list)


def _resolve_institution_id(client: Any, slug: str) -> str:
    existing = (
        client.schema("catalog")
        .table("institutions")
        .select("id")
        .eq("slug", slug)
        .limit(1)
        .execute()
        .data
    )
    if not existing:
        raise RuntimeError(f"Institution not found for slug: {slug!r}")
    return str(existing[0]["id"])


def _ensure_source_course(
    client: Any, institution_id: str, subject: str, number: str
) -> tuple[str, bool]:
    """Select-then-update-or-insert a minimal Bellevue source course row.

    Returns `(course_id, created)`. Never sends `id` on the update path, so an
    existing row's id is never reassigned to our deterministic uuid5 guess.
    """
    query = (
        client.schema("catalog").table("courses").select("id").eq("institution_id", institution_id)
    )
    query = _filter_eq_or_null(query, "campus", _BELLEVUE_CAMPUS)
    existing = query.eq("subject", subject).eq("number", number).limit(1).execute().data
    if existing:
        return str(existing[0]["id"]), False
    key = f"{institution_id}:{_BELLEVUE_CAMPUS}:{subject}:{number}"
    course_id = str(uuid.uuid5(NAMESPACE, key))
    client.schema("catalog").table("courses").insert(
        {
            "id": course_id,
            "institution_id": institution_id,
            "subject": subject,
            "number": number,
            "campus": _BELLEVUE_CAMPUS,
            "active": True,
        }
    ).execute()
    return course_id, True


def _ensure_source_course_version(client: Any, course_id: str, code: str) -> bool:
    """Select-then-insert a minimal `catalog.course_versions` row for a Bellevue
    source course, so it is visible through the `catalog.recommendation_courses`
    view (which JOINs `courses` to `course_versions`).

    Returns `created` (True if a version row was inserted). Never updates an
    existing version's id, and never inserts a second version for a course that
    already has one.

    `title` is set to the course's own code (e.g. "CS 211"), NOT a fabricated
    descriptive name — we never ingested Bellevue's catalog, and the
    equivalency guide's source cell only gives the code, so a real title is
    not available.
    """
    existing = (
        client.schema("catalog")
        .table("course_versions")
        .select("id")
        .eq("course_id", course_id)
        .limit(1)
        .execute()
        .data
    )
    if existing:
        return False
    version_id = str(uuid.uuid5(NAMESPACE, f"{course_id}#v"))
    client.schema("catalog").table("course_versions").insert(
        {
            "id": version_id,
            "course_id": course_id,
            "title": code,
        }
    ).execute()
    return True


def _resolve_uw_course(client: Any, institution_id: str, subject: str, number: str) -> str | None:
    """Look up a UW destination course. Returns `None` if it does not exist — never
    inserts a course here; an unresolved destination becomes a category component."""
    existing = (
        client.schema("catalog")
        .table("courses")
        .select("id")
        .eq("institution_id", institution_id)
        .eq("subject", subject)
        .eq("number", number)
        .limit(1)
        .execute()
        .data
    )
    if existing:
        return str(existing[0]["id"])
    return None


def _upsert_equivalency(
    client: Any,
    intent: EquivalencyIntent,
    *,
    source_institution_id: str,
    destination_institution_id: str,
    review_status: str,
) -> None:
    fields = {
        "source_institution_id": source_institution_id,
        "destination_institution_id": destination_institution_id,
        "mapping_type": intent.mapping_type,
        "credits_awarded": intent.credits_awarded,
        "minimum_grade": intent.minimum_grade,
        "conditions": intent.conditions,
        "confidence": "high",
        "review_status": review_status,
    }
    existing = (
        client.schema("equivalency")
        .table("course_equivalencies")
        .select("id")
        .eq("id", intent.id)
        .limit(1)
        .execute()
        .data
    )
    if existing:
        client.schema("equivalency").table("course_equivalencies").update(fields).eq(
            "id", intent.id
        ).execute()
    else:
        client.schema("equivalency").table("course_equivalencies").insert(
            {"id": intent.id, **fields}
        ).execute()


def _replace_components(
    client: Any,
    intent: EquivalencyIntent,
    *,
    source_course_ids: list[str],
    destination_course_id: str | None,
) -> None:
    """Delete this equivalency's existing components, then insert fresh ones."""
    client.schema("equivalency").table("equivalency_components").delete().eq(
        "equivalency_id", intent.id
    ).execute()

    rows: list[dict[str, Any]] = [
        {
            "equivalency_id": intent.id,
            "component_role": "source",
            "course_id": course_id,
            "position": position,
        }
        for position, course_id in enumerate(source_course_ids)
    ]
    if destination_course_id is not None:
        rows.append(
            {
                "equivalency_id": intent.id,
                "component_role": "destination",
                "course_id": destination_course_id,
                "position": 0,
            }
        )
    else:
        rows.append(
            {
                "equivalency_id": intent.id,
                "component_role": "category",
                "category": intent.destination_outcome,
                "position": 0,
            }
        )
    client.schema("equivalency").table("equivalency_components").insert(rows).execute()


def publish_equivalencies(
    client: Any,
    intents: list[EquivalencyIntent],
    *,
    source_slug: str = "bellevue-college",
    destination_slug: str = "uw-seattle",
    review_status: str = "approved",
) -> PublishReport:
    """Thin executor: write `intents` to a live Supabase `equivalency` schema,
    idempotently. Never fabricates a destination course — unresolvable destinations
    become `category` components."""
    source_institution_id = _resolve_institution_id(client, source_slug)
    destination_institution_id = _resolve_institution_id(client, destination_slug)

    report = PublishReport()
    source_course_id_cache: dict[tuple[str, str], str] = {}

    for intent in intents:
        source_course_ids = []
        for subject, number in intent.source_courses:
            key = (subject, number)
            if key not in source_course_id_cache:
                course_id, created = _ensure_source_course(
                    client, source_institution_id, subject, number
                )
                source_course_id_cache[key] = course_id
                if created:
                    report.source_courses_created += 1
                version_created = _ensure_source_course_version(
                    client, course_id, f"{subject} {number}"
                )
                if version_created:
                    report.source_course_versions_created += 1
            source_course_ids.append(source_course_id_cache[key])

        destination_course_id = None
        if intent.destination is not None:
            subject, number = intent.destination
            destination_course_id = _resolve_uw_course(
                client, destination_institution_id, subject, number
            )

        _upsert_equivalency(
            client,
            intent,
            source_institution_id=source_institution_id,
            destination_institution_id=destination_institution_id,
            review_status=review_status,
        )
        _replace_components(
            client,
            intent,
            source_course_ids=source_course_ids,
            destination_course_id=destination_course_id,
        )

        report.equivalencies_upserted += 1
        if destination_course_id is not None:
            report.destinations_resolved += 1
        else:
            report.destinations_as_category += 1
            report.unresolved_destinations.append(intent.destination_outcome)

    return report


class EquivalencyPublisher:
    """Lazy Supabase client holder; mirrors `SupabasePublisher`."""

    def __init__(self, client: Any) -> None:
        self.client = client

    @classmethod
    def from_env(cls) -> EquivalencyPublisher:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required.")
        from supabase import create_client

        return cls(create_client(url, key))

    def publish(
        self,
        intents: list[EquivalencyIntent],
        *,
        source_slug: str = "bellevue-college",
        destination_slug: str = "uw-seattle",
        review_status: str = "approved",
    ) -> PublishReport:
        return publish_equivalencies(
            self.client,
            intents,
            source_slug=source_slug,
            destination_slug=destination_slug,
            review_status=review_status,
        )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Publish curated Bellevue College -> UW Seattle equivalencies to Supabase."
    )
    parser.add_argument("--review-status", default="approved")
    args = parser.parse_args(argv)

    try:
        from academic_ingest.transfer.curated_equivalencies import curated_records

        records = curated_records().get(("bellevue-college", "uw-seattle"), [])
        intents = build_equivalency_intents(records)
        publisher = EquivalencyPublisher.from_env()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    report = publisher.publish(intents, review_status=args.review_status)
    print(json.dumps(asdict(report), indent=2))


if __name__ == "__main__":
    main()
