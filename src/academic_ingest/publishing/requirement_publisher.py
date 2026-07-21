"""Publish the 21 REAL UW major-admission requirements into Supabase's `policy` schema.

Moves live-crawled UW admission requirements (real course codes, CHOOSE-N groups,
minimum grades) from an ingestion export into `policy.requirements` +
`policy.requirement_courses`, replacing the 5 fictional seed rows those tables
currently hold. Two clearly separated layers, mirroring `supabase_publisher.py` and
`equivalency_publisher.py`:

1. PURE (`build_requirement_intents`) — deterministic, offline-testable, no client/I-O.
2. EXECUTOR (`publish_requirements`) — thin I/O against a live Supabase client. Not
   unit-tested against a real network; the `supabase` package is imported lazily
   (inside `RequirementPublisher.from_env`) so offline pytest runs never need a live
   client. `NAMESPACE`, `slugify`, and `_filter_eq_or_null` are reused directly from
   `supabase_publisher` rather than duplicated; `parse_course_code` is reused from
   `equivalency_publisher`.

The critical join: the requirement payload's `program_id` is an ingestion-internal
UUID that cannot be resolved from the export (the normalized tables are empty).
Instead, each requirement is joined to its program by evidence `source_url`: build a
`{source_url -> program payload official_name}` map from the program records, then
look up each requirement's `evidence[0]["source_url"]` in it. A requirement whose
source_url has no matching program is skipped (never guessed).

`expression_id` on every requirement payload is always null here — there is no parsed
expression tree in this export. `build_requirement_intents` synthesizes a flat, single
level structure (`choose_n` or `all_of`) that records exactly what is known and is
labeled clearly as flattened, not a parsed tree, so nothing downstream mistakes it for
one.

THE CRITICAL RULE: never invent a course or a program. `publish_requirements` never
creates a `catalog.programs` or `catalog.courses` row — a requirement whose program
does not already exist is skipped and recorded in `programs_missing`; an allowed
course code that does not resolve to an existing UW course is skipped and recorded in
`unresolved_courses`.

Idempotency:
  - `policy.requirements`: the row's natural key (program_slug + name) IS the
    deterministic uuid5 `id` on its `RequirementIntent`, so a plain select-by-id then
    update-or-insert is safe here without a separate natural-key lookup — the id used
    to look the row up is exactly the id used to write it, so an existing row's id is
    never reassigned across runs.
  - `policy.requirement_courses`: replaced idempotently per requirement (delete
    existing rows for `requirement_id`, then insert fresh ones) so re-running never
    duplicates or accumulates stale links.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from academic_ingest.publishing.equivalency_publisher import parse_course_code
from academic_ingest.publishing.supabase_publisher import NAMESPACE, _to_float, slugify

# `policy.requirements.scope` is `policy.requirement_scope` (institution, campus,
# college, department, program, major, applicant_type, catalog_year — see
# supabase/migrations/202607160001_initial_backend.sql). Every requirement here has a
# `program_id` FK, so `scope='program'` — the same value `supabase/seed.sql` uses for
# its own program-tied fictional requirement rows.
_REQUIREMENT_SCOPE = "program"

_EXPRESSION_SOURCE = "uw.major_detail"
_EXPRESSION_NOTE = "flattened from admission-requirement bullet; not a parsed expression tree"


# ---------------------------------------------------------------------------
# PURE (offline-testable)
# ---------------------------------------------------------------------------


@dataclass
class RequirementIntent:
    """A single requirement record, joined to its program and given a deterministic id."""

    id: str
    program_slug: str
    name: str
    description: str | None
    requirement_type: str
    expression: dict[str, Any]
    minimum_credits: float | None
    minimum_courses: int | None
    minimum_grade: str | None
    mandatory: bool
    recommended: bool
    allowed_courses: list[str]
    parsed_courses: list[tuple[str, str]]


def _build_program_map(records: list[dict[str, Any]]) -> dict[str, str]:
    """`source_url -> program payload official_name`, built from `program` records."""
    program_by_source_url: dict[str, str] = {}
    for record in records:
        if record.get("record_type") != "program":
            continue
        official_name = (record.get("payload") or {}).get("official_name")
        if not official_name:
            continue
        for evidence in record.get("evidence") or []:
            source_url = evidence.get("source_url")
            if source_url:
                program_by_source_url[source_url] = official_name
    return program_by_source_url


def _build_expression(minimum_courses: int | None, allowed_courses: list[str]) -> dict[str, Any]:
    if minimum_courses is not None and minimum_courses > 0:
        return {
            "kind": "choose_n",
            "n": minimum_courses,
            "courses": allowed_courses,
            "source": _EXPRESSION_SOURCE,
            "note": _EXPRESSION_NOTE,
        }
    return {
        "kind": "all_of",
        "courses": allowed_courses,
        "source": _EXPRESSION_SOURCE,
        "note": _EXPRESSION_NOTE,
    }


def build_requirement_intents(records: list[dict[str, Any]]) -> list[RequirementIntent]:
    """Pure transform: ingestion-export records -> `RequirementIntent`s.

    Requires both `program` and `requirement` records in the same list (the program
    map is built first from the `program` records, then each `requirement` record is
    joined to it by evidence `source_url`). A requirement whose source_url has no
    matching program is skipped.
    """
    program_by_source_url = _build_program_map(records)
    intents: list[RequirementIntent] = []
    for record in records:
        if record.get("record_type") != "requirement":
            continue
        evidence_list = record.get("evidence") or []
        if not evidence_list:
            continue
        source_url = evidence_list[0].get("source_url")
        official_name = program_by_source_url.get(source_url) if source_url else None
        if official_name is None:
            continue

        payload = record.get("payload") or {}
        program_slug = slugify(official_name)
        name = payload.get("name") or ""
        intent_id = str(uuid.uuid5(NAMESPACE, f"{program_slug}|{name}"))

        allowed_courses = list(payload.get("allowed_courses") or [])
        parsed_courses = [
            parsed for code in allowed_courses if (parsed := parse_course_code(code)) is not None
        ]

        minimum_courses = payload.get("minimum_courses")
        expression = _build_expression(minimum_courses, allowed_courses)

        mandatory = bool(payload.get("mandatory"))
        recommended = bool(payload.get("recommended"))
        if mandatory and recommended:
            # Guards the DB CHECK `not (mandatory and recommended)` — mandatory wins.
            recommended = False

        intents.append(
            RequirementIntent(
                id=intent_id,
                program_slug=program_slug,
                name=name,
                description=payload.get("description"),
                requirement_type=payload.get("requirement_type") or "major_admission",
                expression=expression,
                minimum_credits=_to_float(payload.get("minimum_credits")),
                minimum_courses=minimum_courses,
                minimum_grade=payload.get("minimum_grade"),
                mandatory=mandatory,
                recommended=recommended,
                allowed_courses=allowed_courses,
                parsed_courses=parsed_courses,
            )
        )
    return intents


# ---------------------------------------------------------------------------
# EXECUTOR (thin I/O; exercised live against a real Supabase project)
# ---------------------------------------------------------------------------


@dataclass
class PublishReport:
    """Counts returned by the live executor after a `publish_requirements` run."""

    requirements_upserted: int = 0
    requirement_courses_linked: int = 0
    programs_missing: list[str] = field(default_factory=list)
    unresolved_courses: list[str] = field(default_factory=list)


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


def _resolve_program_id(client: Any, institution_id: str, slug: str) -> str | None:
    existing = (
        client.schema("catalog")
        .table("programs")
        .select("id")
        .eq("institution_id", institution_id)
        .eq("slug", slug)
        .limit(1)
        .execute()
        .data
    )
    if existing:
        return str(existing[0]["id"])
    return None


def _resolve_course_id(client: Any, institution_id: str, subject: str, number: str) -> str | None:
    """Look up a UW course. Returns `None` if it does not exist — never inserts one."""
    query = (
        client.schema("catalog").table("courses").select("id").eq("institution_id", institution_id)
    )
    existing = query.eq("subject", subject).eq("number", number).limit(1).execute().data
    if existing:
        return str(existing[0]["id"])
    return None


def _upsert_requirement(
    client: Any, intent: RequirementIntent, *, institution_id: str, program_id: str
) -> None:
    """Select-then-update-or-insert by the intent's own deterministic `id`.

    Safe without a separate natural-key lookup: the id used to look the row up is
    exactly the id used to write it, so an existing row's id is never reassigned.
    """
    fields = {
        "institution_id": institution_id,
        "program_id": program_id,
        "requirement_type": intent.requirement_type,
        "scope": _REQUIREMENT_SCOPE,
        "name": intent.name,
        "description": intent.description,
        "expression": intent.expression,
        "minimum_credits": intent.minimum_credits,
        "minimum_courses": intent.minimum_courses,
        "minimum_grade": intent.minimum_grade,
        "mandatory": intent.mandatory,
        "recommended": intent.recommended,
    }
    existing = (
        client.schema("policy")
        .table("requirements")
        .select("id")
        .eq("id", intent.id)
        .limit(1)
        .execute()
        .data
    )
    if existing:
        client.schema("policy").table("requirements").update(fields).eq("id", intent.id).execute()
    else:
        client.schema("policy").table("requirements").insert({"id": intent.id, **fields}).execute()


def _replace_requirement_courses(client: Any, requirement_id: str, course_ids: list[str]) -> None:
    """Delete this requirement's existing course links, then insert fresh ones."""
    client.schema("policy").table("requirement_courses").delete().eq(
        "requirement_id", requirement_id
    ).execute()
    if not course_ids:
        return
    rows = [
        {
            "requirement_id": requirement_id,
            "course_id": course_id,
            "role": "allowed",
            "priority": position,
        }
        for position, course_id in enumerate(course_ids)
    ]
    client.schema("policy").table("requirement_courses").insert(rows).execute()


def publish_requirements(
    client: Any, intents: list[RequirementIntent], *, institution_slug: str = "uw-seattle"
) -> PublishReport:
    """Thin executor: write `intents` to a live Supabase `policy` schema, idempotently.

    Never fabricates a program or a course: a requirement whose program_slug does not
    resolve to an existing `catalog.programs` row is skipped (`programs_missing`); an
    allowed course code that does not resolve to an existing `catalog.courses` row is
    skipped (`unresolved_courses`), never inserted.
    """
    institution_id = _resolve_institution_id(client, institution_slug)
    report = PublishReport()
    program_id_cache: dict[str, str | None] = {}
    course_id_cache: dict[tuple[str, str], str | None] = {}

    for intent in intents:
        if intent.program_slug not in program_id_cache:
            program_id_cache[intent.program_slug] = _resolve_program_id(
                client, institution_id, intent.program_slug
            )
        program_id = program_id_cache[intent.program_slug]
        if program_id is None:
            report.programs_missing.append(intent.program_slug)
            continue

        _upsert_requirement(client, intent, institution_id=institution_id, program_id=program_id)
        report.requirements_upserted += 1

        course_ids: list[str] = []
        for subject, number in intent.parsed_courses:
            key = (subject, number)
            if key not in course_id_cache:
                course_id_cache[key] = _resolve_course_id(client, institution_id, subject, number)
            course_id = course_id_cache[key]
            if course_id is None:
                report.unresolved_courses.append(f"{subject} {number}")
                continue
            course_ids.append(course_id)

        _replace_requirement_courses(client, intent.id, course_ids)
        report.requirement_courses_linked += len(course_ids)

    return report


class RequirementPublisher:
    """Lazy Supabase client holder; mirrors `SupabasePublisher` / `EquivalencyPublisher`."""

    def __init__(self, client: Any) -> None:
        self.client = client

    @classmethod
    def from_env(cls) -> RequirementPublisher:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required.")
        from supabase import create_client

        return cls(create_client(url, key))

    def publish(
        self, intents: list[RequirementIntent], *, institution_slug: str = "uw-seattle"
    ) -> PublishReport:
        return publish_requirements(self.client, intents, institution_slug=institution_slug)


def _load_program_and_requirement_records(path: str) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    return [
        record
        for record in data.get("records", [])
        if record.get("record_type") in ("program", "requirement")
    ]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Publish real UW major-admission requirements to the Supabase policy schema."
    )
    parser.add_argument("--input", required=True, help="Path to an ingestion export JSON.")
    parser.add_argument("--institution-slug", default="uw-seattle")
    args = parser.parse_args(argv)

    try:
        records = _load_program_and_requirement_records(args.input)
        intents = build_requirement_intents(records)
        publisher = RequirementPublisher.from_env()
    except FileNotFoundError as exc:
        print(f"Error: input file not found: {exc.filename}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    report = publisher.publish(intents, institution_slug=args.institution_slug)
    print(json.dumps(asdict(report), indent=2))


if __name__ == "__main__":
    main()
