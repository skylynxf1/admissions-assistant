"""Bounded publisher: real UW courses + programs -> Supabase `catalog` schema.

Scope is COURSES + PROGRAMS only. Prerequisites, requirements, equivalencies,
offerings, and evidence/source rows are explicitly deferred — they need
parsing/FK logic that doesn't exist yet.

Two clearly separated layers:

1. PURE (`build_catalog_rows`) — deterministic, offline-testable, no client/I-O.
   Takes ingestion-export records and returns plain dict rows shaped for the
   `catalog.courses`, `catalog.course_versions`, and `catalog.programs` tables,
   plus a couple of executor-only helper keys (`institution_slug`,
   `canonical_key`) used to resolve real database ids.

2. EXECUTOR (`publish_catalog`) — thin I/O against a live Supabase client. Not
   unit-tested against a real network; the `supabase` package is imported
   lazily (inside `SupabasePublisher.from_env`) so offline pytest runs never
   need a live client, mirroring
   `services/course-recommendation/app/repository.py`.

Idempotency:
  - Courses are select-then-update-or-insert by the natural key
    `(institution_id, campus, subject, number)`, same pattern as programs below.
    An `on_conflict` upsert that includes `id` is NOT safe here: if a row
    already exists at that natural key (e.g. seeded) with a different id than
    our deterministic uuid5 guess, PostgREST would try to update the existing
    row's `id` to our guess, which fails with `course_versions_course_id_fkey`
    (23503) the moment any course_versions row already references the existing
    id. Selecting first and updating by the row's own id (or inserting fresh
    with the deterministic id when absent) means an existing row's id is never
    reassigned.
  - Course versions are select-then-update-or-insert by `course_id` (the
    resolved id from the courses step above), for the same reason: avoids ever
    reassigning `id` on an existing row, and avoids creating duplicate version
    rows on re-run.
  - Programs are select-then-update-or-insert by `(institution_id, slug)`: the
    `catalog.programs` unique constraint is `(institution_id, slug,
    catalog_version_id)` and `catalog_version_id` is NULL for these rows, so
    Postgres would NOT reject a duplicate `(institution_id, slug)` pair via
    on_conflict (NULLs are distinct in unique constraints) — an on_conflict
    upsert would silently double-insert. `supabase/seed.sql` already seeds a
    uw-seattle program with slug "computer-science", so this path is exercised
    on the very first run.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import uuid
from dataclasses import dataclass, field
from typing import Any

# Fixed namespace for uuid5-derived deterministic ids. Any fixed literal works;
# this is the RFC 4122 example namespace, reused here only as a stable constant.
NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

_SLUG_COLLAPSE_RE = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    """Lowercase; collapse runs of non-alphanumeric characters to a single '-'; strip."""
    return _SLUG_COLLAPSE_RE.sub("-", value.strip().lower()).strip("-")


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(result):
        return None
    return result


@dataclass
class CatalogRows:
    """Plain-dict rows produced by `build_catalog_rows`, grouped by target table."""

    courses: list[dict[str, Any]] = field(default_factory=list)
    course_versions: list[dict[str, Any]] = field(default_factory=list)
    programs: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class PublishReport:
    """Counts returned by the live executor after a `publish_catalog` run."""

    institution_id: str
    courses_upserted: int = 0
    course_versions_upserted: int = 0
    programs_upserted: int = 0


def build_catalog_rows(records: list[dict[str, Any]], *, institution_id: str) -> CatalogRows:
    """Pure transform: ingestion-export records -> catalog table rows.

    `institution_id` here is the institution's natural-key slug (e.g.
    "uw-seattle") as it appears on each record's payload, not a resolved
    database uuid — the executor resolves the real uuid separately. It is
    carried through on each row as `institution_slug` for the executor to use.

    Non-course/non-program records are ignored (scope is bounded to courses +
    programs; the caller is also expected to pre-filter, but this stays
    defensive so callers don't have to).
    """
    rows = CatalogRows()
    for record in records:
        record_type = record.get("record_type")
        canonical_key = record["canonical_key"]
        payload = record.get("payload") or {}
        if record_type == "course":
            rows.courses.append(_build_course_row(canonical_key, payload, institution_id))
            rows.course_versions.append(_build_course_version_row(canonical_key, payload))
        elif record_type == "program":
            rows.programs.append(_build_program_row(canonical_key, payload, institution_id))
    return rows


def _build_course_row(
    canonical_key: str, payload: dict[str, Any], institution_slug: str
) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid5(NAMESPACE, canonical_key)),
        "canonical_key": canonical_key,
        "institution_slug": institution_slug,
        "subject": payload.get("subject"),
        "number": payload.get("number"),
        "campus": payload.get("campus"),
        "active": True,
        "credit_system": payload.get("credit_type"),
    }


def _build_course_version_row(canonical_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    level = payload.get("level")
    return {
        "id": str(uuid.uuid5(NAMESPACE, canonical_key + "#v")),
        "course_ref": canonical_key,
        "title": payload.get("title"),
        "description": payload.get("description"),
        "credits_min": _to_float(payload.get("credits_min")),
        "credits_max": _to_float(payload.get("credits_max")),
        "course_level": str(level) if level is not None else None,
        "general_education_designators": list(payload.get("general_education_designators") or []),
        "equivalent_course_ids": [],
    }


def _build_program_row(
    canonical_key: str, payload: dict[str, Any], institution_slug: str
) -> dict[str, Any]:
    official_name = payload.get("official_name") or ""
    return {
        "id": str(uuid.uuid5(NAMESPACE, canonical_key)),
        "institution_slug": institution_slug,
        "slug": slugify(official_name),
        "name": official_name,
        "program_type": "major",
        "degree_type": payload.get("degree_type"),
        "capacity_status": (
            "capacity-constrained" if payload.get("major_type") == "capacity_constrained" else None
        ),
        "application_required": bool(payload.get("application_required") or False),
        "active": True,
    }


# ---------------------------------------------------------------------------
# EXECUTOR (thin I/O; exercised live against a real Supabase project)
# ---------------------------------------------------------------------------


def _filter_eq_or_null(query: Any, column: str, value: Any) -> Any:
    """Apply an equality filter on `column` that also matches a real SQL NULL.

    postgrest-py stringifies filter values, so `.eq(column, None)` becomes the
    literal query string `column=eq.None`, which never matches a NULL row.
    Nullable natural-key columns (e.g. `catalog.courses.campus`) must instead
    use PostgREST's `is`-null filter when the Python value is `None`.
    """
    if value is None:
        return query.is_(column, "null")
    return query.eq(column, value)


def _resolve_institution_id(client: Any, institution_slug: str) -> str:
    existing = (
        client.schema("catalog")
        .table("institutions")
        .select("id")
        .eq("slug", institution_slug)
        .limit(1)
        .execute()
        .data
    )
    if existing:
        return str(existing[0]["id"])
    inserted = (
        client.schema("catalog")
        .table("institutions")
        # institution_type has no default and is NOT NULL; "unknown" is a
        # deliberately neutral placeholder for institutions the publisher
        # creates itself (normally seed.sql or an admin flow sets the real
        # institution_type before this path is ever hit).
        .insert({"slug": institution_slug, "name": institution_slug, "institution_type": "unknown"})
        .execute()
        .data
    )
    return str(inserted[0]["id"])


def _upsert_courses(
    client: Any, courses: list[dict[str, Any]], institution_id: str
) -> tuple[int, dict[str, str]]:
    """Select-then-update-or-insert each course by its natural key.

    Never sends `id` in an update, so an existing row's id (e.g. seeded, or
    from a prior run) is never reassigned to our deterministic uuid5 guess —
    see the module docstring's Idempotency note for why an on_conflict upsert
    is unsafe here.

    Returns (count processed, canonical_key -> resolved course id map) so the
    caller can attach course_versions to the *actual* database id rather than
    the deterministic guess.
    """
    course_id_by_canonical_key: dict[str, str] = {}
    for row in courses:
        fields = {
            "active": row["active"],
            "credit_system": row["credit_system"],
        }
        query = (
            client.schema("catalog")
            .table("courses")
            .select("id")
            .eq("institution_id", institution_id)
        )
        query = _filter_eq_or_null(query, "campus", row["campus"])
        existing = (
            query.eq("subject", row["subject"]).eq("number", row["number"]).limit(1).execute().data
        )
        if existing:
            course_id = str(existing[0]["id"])
            client.schema("catalog").table("courses").update(fields).eq("id", course_id).execute()
        else:
            course_id = row["id"]
            client.schema("catalog").table("courses").insert(
                {
                    "id": course_id,
                    "institution_id": institution_id,
                    "subject": row["subject"],
                    "number": row["number"],
                    "campus": row["campus"],
                    **fields,
                }
            ).execute()
        course_id_by_canonical_key[row["canonical_key"]] = course_id
    return len(courses), course_id_by_canonical_key


def _upsert_course_versions(
    client: Any,
    course_versions: list[dict[str, Any]],
    course_id_by_canonical_key: dict[str, str],
) -> int:
    """Select-then-update-or-insert each version by its resolved `course_id`.

    Mirrors `_upsert_courses`: never reassigns an existing row's `id`, and
    (unlike an on_conflict="id" upsert against our deterministic guess) never
    creates a duplicate version row when the course already resolved to a
    pre-existing id on a prior run.
    """
    count = 0
    for row in course_versions:
        course_id = course_id_by_canonical_key.get(row["course_ref"])
        if course_id is None:
            # Shouldn't happen (every version is built from a course in the same
            # batch), but skip defensively rather than upsert an orphan.
            continue
        fields = {
            "title": row["title"],
            "description": row["description"],
            "credits_min": row["credits_min"],
            "credits_max": row["credits_max"],
            "course_level": row["course_level"],
            "general_education_designators": row["general_education_designators"],
            "equivalent_course_ids": row["equivalent_course_ids"],
        }
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
            version_id = existing[0]["id"]
            client.schema("catalog").table("course_versions").update(fields).eq(
                "id", version_id
            ).execute()
        else:
            client.schema("catalog").table("course_versions").insert(
                {"id": row["id"], "course_id": course_id, **fields}
            ).execute()
        count += 1
    return count


def _upsert_program(client: Any, row: dict[str, Any], institution_id: str) -> None:
    fields = {
        "name": row["name"],
        "program_type": row["program_type"],
        "degree_type": row["degree_type"],
        "capacity_status": row["capacity_status"],
        "application_required": row["application_required"],
        "active": row["active"],
    }
    existing = (
        client.schema("catalog")
        .table("programs")
        .select("id")
        .eq("institution_id", institution_id)
        .eq("slug", row["slug"])
        .limit(1)
        .execute()
        .data
    )
    if existing:
        program_id = existing[0]["id"]
        client.schema("catalog").table("programs").update(fields).eq("id", program_id).execute()
    else:
        client.schema("catalog").table("programs").insert(
            {"id": row["id"], "institution_id": institution_id, "slug": row["slug"], **fields}
        ).execute()


def publish_catalog(
    client: Any, rows: CatalogRows, *, institution_slug: str = "uw-seattle"
) -> PublishReport:
    """Thin executor: write `rows` to a live Supabase `catalog` schema, idempotently."""
    institution_id = _resolve_institution_id(client, institution_slug)

    courses_upserted, course_id_by_canonical_key = _upsert_courses(
        client, rows.courses, institution_id
    )
    course_versions_upserted = _upsert_course_versions(
        client, rows.course_versions, course_id_by_canonical_key
    )

    for program_row in rows.programs:
        _upsert_program(client, program_row, institution_id)

    return PublishReport(
        institution_id=institution_id,
        courses_upserted=courses_upserted,
        course_versions_upserted=course_versions_upserted,
        programs_upserted=len(rows.programs),
    )


class SupabasePublisher:
    """Lazy Supabase client holder; mirrors `SupabaseRecommendationRepository`."""

    def __init__(self, client: Any) -> None:
        self.client = client

    @classmethod
    def from_env(cls) -> SupabasePublisher:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required.")
        from supabase import create_client

        return cls(create_client(url, key))

    def publish(self, rows: CatalogRows, *, institution_slug: str = "uw-seattle") -> PublishReport:
        return publish_catalog(self.client, rows, institution_slug=institution_slug)


def _load_course_and_program_records(path: str) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    return [
        record
        for record in data.get("records", [])
        if record.get("record_type") in ("course", "program")
    ]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Publish real UW courses + programs to the Supabase catalog schema."
    )
    parser.add_argument("--input", required=True, help="Path to an ingestion export JSON.")
    parser.add_argument("--institution-slug", default="uw-seattle")
    args = parser.parse_args(argv)

    try:
        records = _load_course_and_program_records(args.input)
        rows = build_catalog_rows(records, institution_id=args.institution_slug)
        publisher = SupabasePublisher.from_env()
    except FileNotFoundError as exc:
        print(f"Error: input file not found: {exc.filename}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    report = publisher.publish(rows, institution_slug=args.institution_slug)
    print(
        json.dumps(
            {
                "institution_id": report.institution_id,
                "courses_upserted": report.courses_upserted,
                "course_versions_upserted": report.course_versions_upserted,
                "programs_upserted": report.programs_upserted,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
