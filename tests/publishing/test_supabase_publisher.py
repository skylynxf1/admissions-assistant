"""Offline tests for the pure `build_catalog_rows` layer of the bounded publisher.

These records are copied verbatim (record_type/canonical_key/payload only) from the
real UW ingestion export at .superpowers/sdd/pubdata/uw_records.json, trimmed to the
fields build_catalog_rows actually reads, per the brief's guidance to inline
representative records rather than depend on the scratch file's path.

The executor (`publish_catalog`) does live Supabase I/O and is intentionally not
unit-tested here (import of `supabase` is lazy and only happens inside `from_env`).
"""

from __future__ import annotations

import json
import math
import uuid
from typing import Any

import pytest

from academic_ingest.publishing.supabase_publisher import (
    NAMESPACE,
    _filter_eq_or_null,
    _to_float,
    _upsert_courses,
    build_catalog_rows,
    main,
    slugify,
)

CSE_143 = {
    "record_type": "course",
    "canonical_key": "uw-seattle:CSE 143",
    "payload": {
        "subject": "CSE",
        "number": "143",
        "campus": "Seattle",
        "title": "Computer Programming II",
        "description": "Continuation of CSE 142.",
        "credits_min": "5",
        "credits_max": "5",
        "credit_type": "quarter",
        "level": 100,
        "general_education_designators": ["NSc", "RSN"],
        "equivalent_courses": ["CSS 143", "TCSS 143"],
        "prerequisite_text": "CSE 142.",
        "institution_id": "uw-seattle",
    },
}

CSE_4XX = {
    "record_type": "course",
    "canonical_key": "uw-seattle:CSE 4XX",
    "payload": {
        "subject": "CSE",
        "number": "4XX",
        "campus": "Seattle",
        "title": "Evidence-Preserving Systems",
        "description": "Builds bounded academic data systems.",
        "credits_min": "3",
        "credits_max": "5",
        "credit_type": "quarter",
        "level": 400,
        "general_education_designators": ["DIV"],
        "equivalent_courses": [],
        "prerequisite_text": "CSE 143 and INFO 200.",
        "institution_id": "uw-seattle",
    },
}

INFO_180 = {
    "record_type": "course",
    "canonical_key": "uw-seattle:INFO 180",
    "payload": {
        "subject": "INFO",
        "number": "180",
        "campus": "Seattle",
        "title": "Introduction to Data Science",
        "description": "Introduces data science across social and technical contexts.",
        "credits_min": "4",
        "credits_max": "4",
        "credit_type": "quarter",
        "level": 100,
        "general_education_designators": ["RSN"],
        "equivalent_courses": ["CSE 180", "STAT 180"],
        "prerequisite_text": None,
        "institution_id": "uw-seattle",
    },
}

INFO_200 = {
    "record_type": "course",
    "canonical_key": "uw-seattle:INFO 200",
    "payload": {
        "subject": "INFO",
        "number": "200",
        "campus": "Seattle",
        "title": "Intellectual Foundations of Informatics",
        "description": "Examines information as an object and social phenomenon.",
        "credits_min": "5",
        "credits_max": "5",
        "credit_type": "quarter",
        "level": 200,
        "general_education_designators": ["SSc"],
        "equivalent_courses": [],
        "prerequisite_text": None,
        "institution_id": "uw-seattle",
    },
}

COMPUTER_ENGINEERING = {
    "record_type": "program",
    "canonical_key": "uw-seattle:computer engineering",
    "payload": {
        "official_name": "Computer Engineering",
        "campus": "Seattle",
        "major_type": "capacity_constrained",
        "capacity_status": "Computer Engineering Major type: Capacity-constrained",
        "degree_type": None,
        "application_required": None,
        "institution_id": "uw-seattle",
    },
}

COMPUTER_SCIENCE = {
    "record_type": "program",
    "canonical_key": "uw-seattle:computer science",
    "payload": {
        "official_name": "Computer Science",
        "campus": "Seattle",
        "major_type": "capacity_constrained",
        "capacity_status": (
            "Computer Science Major type: Capacity-constrained "
            "The design of software systems and applications."
        ),
        "degree_type": None,
        "application_required": None,
        "institution_id": "uw-seattle",
    },
}

MATHEMATICS = {
    "record_type": "program",
    "canonical_key": "uw-seattle:mathematics",
    "payload": {
        "official_name": "Mathematics",
        "campus": "Seattle",
        "major_type": "minimum_requirements",
        "capacity_status": "Mathematics Major type: Minimum requirements",
        "degree_type": None,
        "application_required": None,
        "institution_id": "uw-seattle",
    },
}

STATISTICS = {
    "record_type": "program",
    "canonical_key": "uw-seattle:statistics",
    "payload": {
        "official_name": "Statistics",
        "campus": "Seattle",
        "major_type": "capacity_constrained",
        "capacity_status": "Statistics Major type: Capacity-constrained",
        "degree_type": None,
        "application_required": None,
        "institution_id": "uw-seattle",
    },
}

# A non-course/program record that build_catalog_rows must ignore.
ADMISSIONS_RULE = {
    "record_type": "admissions_rule",
    "canonical_key": "uw-seattle:transfer:applicant_definition:Transfer applicant definition",
    "payload": {"institution_id": "uw-seattle", "value": "irrelevant"},
}

ALL_RECORDS = [
    ADMISSIONS_RULE,
    CSE_143,
    CSE_4XX,
    INFO_180,
    INFO_200,
    COMPUTER_ENGINEERING,
    COMPUTER_SCIENCE,
    MATHEMATICS,
    STATISTICS,
]


def test_build_catalog_rows_produces_four_courses_and_four_programs() -> None:
    rows = build_catalog_rows(ALL_RECORDS, institution_id="uw-seattle")

    assert len(rows.courses) == 4
    assert len(rows.course_versions) == 4
    assert len(rows.programs) == 4


def test_build_catalog_rows_course_fields() -> None:
    rows = build_catalog_rows([CSE_143], institution_id="uw-seattle")
    course = rows.courses[0]

    assert course["subject"] == "CSE"
    assert course["number"] == "143"
    assert course["campus"] == "Seattle"
    assert course["credit_system"] == "quarter"
    assert course["active"] is True
    assert "canonical_code" not in course


def test_build_catalog_rows_course_ids_are_deterministic_uuid5() -> None:
    rows = build_catalog_rows([CSE_143], institution_id="uw-seattle")
    expected_course_id = str(uuid.uuid5(NAMESPACE, "uw-seattle:CSE 143"))
    expected_version_id = str(uuid.uuid5(NAMESPACE, "uw-seattle:CSE 143#v"))

    assert rows.courses[0]["id"] == expected_course_id
    assert rows.course_versions[0]["id"] == expected_version_id


def test_build_catalog_rows_is_deterministic_across_calls() -> None:
    first = build_catalog_rows(ALL_RECORDS, institution_id="uw-seattle")
    second = build_catalog_rows(ALL_RECORDS, institution_id="uw-seattle")

    assert [c["id"] for c in first.courses] == [c["id"] for c in second.courses]
    assert [v["id"] for v in first.course_versions] == [v["id"] for v in second.course_versions]
    assert [p["id"] for p in first.programs] == [p["id"] for p in second.programs]


def test_build_catalog_rows_course_version_fields() -> None:
    rows = build_catalog_rows([CSE_143], institution_id="uw-seattle")
    version = rows.course_versions[0]

    assert version["title"] == "Computer Programming II"
    assert version["description"] == "Continuation of CSE 142."
    assert version["credits_min"] == 5.0
    assert version["credits_max"] == 5.0
    assert isinstance(version["credits_min"], float)
    assert version["general_education_designators"] == ["NSc", "RSN"]
    assert version["equivalent_course_ids"] == []
    assert version["course_ref"] == "uw-seattle:CSE 143"


def test_build_catalog_rows_tolerates_non_numeric_credits() -> None:
    payload = dict(CSE_143["payload"])
    payload["credits_min"] = None
    payload["credits_max"] = "not-a-number"
    record = {**CSE_143, "payload": payload}

    rows = build_catalog_rows([record], institution_id="uw-seattle")
    version = rows.course_versions[0]

    assert version["credits_min"] is None
    assert version["credits_max"] is None


def test_build_catalog_rows_program_fields_computer_engineering() -> None:
    rows = build_catalog_rows([COMPUTER_ENGINEERING], institution_id="uw-seattle")
    program = rows.programs[0]

    assert program["slug"] == "computer-engineering"
    assert program["name"] == "Computer Engineering"
    assert program["program_type"] == "major"
    assert program["capacity_status"] == "capacity-constrained"
    assert program["application_required"] is False
    assert program["degree_type"] is None
    assert program["active"] is True


def test_build_catalog_rows_program_capacity_status_none_for_minimum_requirements() -> None:
    rows = build_catalog_rows([MATHEMATICS], institution_id="uw-seattle")
    program = rows.programs[0]

    assert program["slug"] == "mathematics"
    assert program["capacity_status"] is None


def test_build_catalog_rows_program_ids_are_deterministic_uuid5() -> None:
    rows = build_catalog_rows([COMPUTER_ENGINEERING], institution_id="uw-seattle")
    expected_id = str(uuid.uuid5(NAMESPACE, "uw-seattle:computer engineering"))

    assert rows.programs[0]["id"] == expected_id


def test_build_catalog_rows_ignores_non_course_non_program_records() -> None:
    rows = build_catalog_rows([ADMISSIONS_RULE], institution_id="uw-seattle")

    assert rows.courses == []
    assert rows.course_versions == []
    assert rows.programs == []


def test_slugify_basic() -> None:
    assert slugify("Computer Engineering") == "computer-engineering"


def test_slugify_collapses_punctuation_and_whitespace() -> None:
    assert slugify("  Data   Science & Analytics!! ") == "data-science-analytics"


def test_slugify_computer_science_collides_with_seeded_program_slug() -> None:
    # supabase/seed.sql already inserts a uw-seattle program with slug
    # "computer-science" (id 20000000-0000-0000-0000-000000000002). The executor
    # must select-then-update-or-insert by (institution_id, slug) rather than blindly
    # inserting a new row with the deterministic id, or this collides.
    assert slugify("Computer Science") == "computer-science"


# ---------------------------------------------------------------------------
# _to_float: reject non-finite strings
# ---------------------------------------------------------------------------


def test_to_float_rejects_nan_string() -> None:
    assert _to_float("nan") is None


def test_to_float_rejects_inf_string() -> None:
    assert _to_float("inf") is None
    assert _to_float("-inf") is None
    assert _to_float("Infinity") is None


def test_to_float_accepts_ordinary_numeric_string() -> None:
    result = _to_float("5")
    assert result == 5.0
    assert result is not None and math.isfinite(result)


# ---------------------------------------------------------------------------
# _filter_eq_or_null: null-safe natural-key filter (fix for the nullable
# `catalog.courses.campus` lookup — postgrest-py's `.eq(col, None)`
# stringifies to the literal "col=eq.None", which never matches a real NULL).
# A minimal stub query-builder records which filter method was invoked so
# this is provable offline, with no network access.
# ---------------------------------------------------------------------------


class _RecordingQuery:
    """Stand-in for a postgrest-py query builder: records `eq`/`is_` calls."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, Any]] = []

    def eq(self, column: str, value: Any) -> _RecordingQuery:
        self.calls.append(("eq", column, value))
        return self

    def is_(self, column: str, value: Any) -> _RecordingQuery:
        self.calls.append(("is_", column, value))
        return self


def test_filter_eq_or_null_uses_is_branch_when_value_is_none() -> None:
    query = _RecordingQuery()

    result = _filter_eq_or_null(query, "campus", None)

    assert result.calls == [("is_", "campus", "null")]


def test_filter_eq_or_null_uses_eq_branch_when_value_is_present() -> None:
    query = _RecordingQuery()

    result = _filter_eq_or_null(query, "campus", "Seattle")

    assert result.calls == [("eq", "campus", "Seattle")]


# ---------------------------------------------------------------------------
# _upsert_courses: end-to-end (fake client) proof that a null-campus course
# is looked up with the `is_` branch and therefore matches an existing NULL
# row instead of always falling through to INSERT (which, on a second run,
# would crash on a primary-key collision with the deterministic uuid5 id).
# ---------------------------------------------------------------------------


class _FakeExecuteResult:
    def __init__(self, data: list[dict[str, Any]]) -> None:
        self.data = data


class _FakeTableQuery:
    """Fakes the chained select/eq/is_/limit/execute and insert/update/execute
    surface `_upsert_courses` calls against a postgrest-py table builder."""

    def __init__(self, table: _FakeTable, op: str, payload: Any = None) -> None:
        self._table = table
        self._op = op
        self._payload = payload
        self.filters: list[tuple[str, str, Any]] = []

    def select(self, *_args: Any) -> _FakeTableQuery:
        return self

    def eq(self, column: str, value: Any) -> _FakeTableQuery:
        self.filters.append(("eq", column, value))
        return self

    def is_(self, column: str, value: Any) -> _FakeTableQuery:
        self.filters.append(("is_", column, value))
        return self

    def limit(self, *_args: Any) -> _FakeTableQuery:
        return self

    def execute(self) -> _FakeExecuteResult:
        if self._op == "select":
            self._table.recorded_select_filters.append(self.filters)
            return _FakeExecuteResult(self._table.existing_rows)
        if self._op == "insert":
            self._table.inserted.append(self._payload)
            return _FakeExecuteResult([])
        if self._op == "update":
            self._table.updated.append((self._payload, self.filters))
            return _FakeExecuteResult([])
        raise AssertionError(f"unexpected op {self._op!r}")  # pragma: no cover


class _FakeTable:
    def __init__(self, existing_rows: list[dict[str, Any]] | None = None) -> None:
        self.existing_rows: list[dict[str, Any]] = existing_rows or []
        self.recorded_select_filters: list[list[tuple[str, str, Any]]] = []
        self.inserted: list[Any] = []
        self.updated: list[Any] = []

    def select(self, *_args: Any) -> _FakeTableQuery:
        return _FakeTableQuery(self, "select")

    def insert(self, payload: Any) -> _FakeTableQuery:
        return _FakeTableQuery(self, "insert", payload)

    def update(self, payload: Any) -> _FakeTableQuery:
        return _FakeTableQuery(self, "update", payload)


class _FakeSchema:
    def __init__(self) -> None:
        self.tables: dict[str, _FakeTable] = {}

    def table(self, name: str) -> _FakeTable:
        return self.tables.setdefault(name, _FakeTable())


class _FakeClient:
    def __init__(self) -> None:
        self.catalog = _FakeSchema()

    def schema(self, name: str) -> _FakeSchema:
        assert name == "catalog"
        return self.catalog


_NULL_CAMPUS_COURSE_ROW = {
    "id": "11111111-1111-1111-1111-111111111111",
    "canonical_key": "uw-online:CSE 100",
    "subject": "CSE",
    "number": "100",
    "campus": None,
    "active": True,
    "credit_system": "quarter",
}


def test_upsert_courses_selects_null_campus_row_with_is_filter() -> None:
    client = _FakeClient()

    _upsert_courses(client, [_NULL_CAMPUS_COURSE_ROW], "institution-uuid")

    select_filters = client.catalog.tables["courses"].recorded_select_filters[0]
    campus_filter = next(f for f in select_filters if f[1] == "campus")
    assert campus_filter == ("is_", "campus", "null")


def test_upsert_courses_matches_existing_null_campus_row_instead_of_reinserting() -> None:
    client = _FakeClient()
    client.catalog.tables["courses"] = _FakeTable(existing_rows=[{"id": "existing-course-uuid"}])

    count, id_map = _upsert_courses(client, [_NULL_CAMPUS_COURSE_ROW], "institution-uuid")

    courses_table = client.catalog.tables["courses"]
    assert count == 1
    # Matched the existing NULL-campus row's real id, not the deterministic guess.
    assert id_map["uw-online:CSE 100"] == "existing-course-uuid"
    # No INSERT was attempted -- this is exactly the case that used to crash on
    # a second run with a primary-key collision (23505) because the old
    # `.eq("campus", None)` filter never matched the real NULL row, so every
    # run fell through to INSERT with the same deterministic uuid5 id.
    assert courses_table.inserted == []
    assert len(courses_table.updated) == 1


def test_upsert_courses_inserts_new_null_campus_row_when_none_exists() -> None:
    client = _FakeClient()

    count, id_map = _upsert_courses(client, [_NULL_CAMPUS_COURSE_ROW], "institution-uuid")

    courses_table = client.catalog.tables["courses"]
    assert count == 1
    assert id_map["uw-online:CSE 100"] == _NULL_CAMPUS_COURSE_ROW["id"]
    assert len(courses_table.inserted) == 1
    assert courses_table.updated == []


# ---------------------------------------------------------------------------
# main(): clean one-line errors instead of raw tracebacks
# ---------------------------------------------------------------------------


def test_main_missing_input_file_exits_1_with_clean_message(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--input", "does/not/exist.json"])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert captured.err.strip() != ""
    assert "Traceback" not in captured.err
    assert "does/not/exist.json" in captured.err


def test_main_missing_supabase_env_exits_1_with_clean_message(
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    input_path = tmp_path / "export.json"
    input_path.write_text(json.dumps({"records": []}), encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        main(["--input", str(input_path)])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert captured.err.strip() != ""
    assert "Traceback" not in captured.err
    assert "SUPABASE_URL" in captured.err
