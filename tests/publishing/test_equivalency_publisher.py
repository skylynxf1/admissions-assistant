"""Offline tests for `equivalency_publisher.py`.

The pure layer (`parse_course_code`, `parse_destination`, `build_equivalency_intents`)
is deterministic and offline-testable per the brief's TDD section. The executor
(`publish_equivalencies`) does live Supabase I/O; it is exercised here only against a
minimal in-memory fake client (no network), mirroring the fake-client pattern already
used in `tests/publishing/test_supabase_publisher.py`.
"""

from __future__ import annotations

import uuid
from typing import Any

from academic_ingest.publishing.equivalency_publisher import (
    NAMESPACE,
    EquivalencyIntent,
    build_equivalency_intents,
    parse_course_code,
    parse_destination,
    publish_equivalencies,
)
from academic_ingest.transfer.models import EquivalencyRecord

# ---------------------------------------------------------------------------
# parse_course_code
# ---------------------------------------------------------------------------


def test_parse_course_code_with_ampersand_subject() -> None:
    assert parse_course_code("MATH& 151") == ("MATH&", "151")


def test_parse_course_code_simple() -> None:
    assert parse_course_code("CS 101") == ("CS", "101")


def test_parse_course_code_multi_word_subject() -> None:
    assert parse_course_code("ART H 201") == ("ART H", "201")


def test_parse_course_code_alphanumeric_number() -> None:
    assert parse_course_code("NURS 100X") == ("NURS", "100X")


def test_parse_course_code_junk_returns_none() -> None:
    assert parse_course_code("no digits here") is None


# ---------------------------------------------------------------------------
# parse_destination
# ---------------------------------------------------------------------------


def test_parse_destination_strips_uw_prefix_and_resolves() -> None:
    assert parse_destination("UW MATH 124") == ("MATH", "124")


def test_parse_destination_no_credit_is_none() -> None:
    assert parse_destination("No credit") is None


def test_parse_destination_generic_wildcard_is_none() -> None:
    assert parse_destination("UW 1XX (LC)") is None


def test_parse_destination_department_wildcard_is_none() -> None:
    assert parse_destination("ART 1XX") is None


def test_parse_destination_ignores_trailing_source_alternatives_prose() -> None:
    assert parse_destination("FRENCH 101 (5) for either FRCH& 121 or FRCH 131") == (
        "FRENCH",
        "101",
    )


def test_parse_destination_simple_with_credits_suffix() -> None:
    assert parse_destination("MATH 124 (5)") == ("MATH", "124")


def test_parse_destination_multi_word_subject() -> None:
    assert parse_destination("BIO A 201 (5)") == ("BIO A", "201")


def test_parse_destination_no_leading_code_is_none() -> None:
    assert parse_destination("No credit") is None


def test_parse_destination_genuine_destination_alternation_is_none() -> None:
    assert parse_destination("ANTH 203 (5) or LING 203 (5)") is None


def test_parse_destination_wildcard_alternation_is_none() -> None:
    assert parse_destination("PHIL 2XX or ART 2XX") is None


# ---------------------------------------------------------------------------
# build_equivalency_intents
# ---------------------------------------------------------------------------

_DIRECT_RECORD = EquivalencyRecord(
    source_course_codes=["MATH& 151"],
    mapping_type="direct_equivalent",
    destination_outcome="UW MATH 124",
    credits_awarded=5.0,
    conditions={"guide_notation": "NSc [RSN]"},
    evidence_refs=["https://example.edu/guide (retrieved 2026-07-20)"],
)

_SEQUENCE_RECORD = EquivalencyRecord(
    source_course_codes=["CS 101", "CS 102"],
    mapping_type="sequence_equivalent",
    destination_outcome="UW CSE 142",
    credits_awarded=10.0,
    evidence_refs=["https://example.edu/guide (retrieved 2026-07-20)"],
)

_NO_CREDIT_RECORD = EquivalencyRecord(
    source_course_codes=["BUS 145"],
    mapping_type="no_credit",
    destination_outcome="No credit",
)


def test_build_equivalency_intents_deterministic_ids_stable_across_calls() -> None:
    first = build_equivalency_intents([_DIRECT_RECORD])
    second = build_equivalency_intents([_DIRECT_RECORD])

    assert first[0].id == second[0].id
    expected_id = str(uuid.uuid5(NAMESPACE, "MATH& 151=>UW MATH 124"))
    assert first[0].id == expected_id


def test_build_equivalency_intents_sequence_record_yields_two_source_entries() -> None:
    intents = build_equivalency_intents([_SEQUENCE_RECORD])

    assert intents[0].source_courses == [("CS", "101"), ("CS", "102")]


def test_build_equivalency_intents_no_credit_record_has_none_destination() -> None:
    intents = build_equivalency_intents([_NO_CREDIT_RECORD])

    assert intents[0].destination is None
    assert intents[0].destination_outcome == "No credit"


def test_build_equivalency_intents_carries_through_fields() -> None:
    intents = build_equivalency_intents([_DIRECT_RECORD])
    intent = intents[0]

    assert isinstance(intent, EquivalencyIntent)
    assert intent.source_courses == [("MATH&", "151")]
    assert intent.destination == ("MATH", "124")
    assert intent.mapping_type == "direct_equivalent"
    assert intent.credits_awarded == 5.0
    assert intent.minimum_grade is None
    assert intent.conditions == {"guide_notation": "NSc [RSN]"}
    assert intent.evidence_refs == ["https://example.edu/guide (retrieved 2026-07-20)"]


# ---------------------------------------------------------------------------
# publish_equivalencies executor: minimal in-memory fake client (no network)
# ---------------------------------------------------------------------------


class _FakeExecuteResult:
    def __init__(self, data: list[dict[str, Any]]) -> None:
        self.data = data


class _FakeQuery:
    """Fakes the chained select/eq/is_/limit/execute and insert/update/delete
    surface that `publish_equivalencies` calls against a postgrest-py table builder."""

    def __init__(self, table: _FakeTable, op: str, payload: Any = None) -> None:
        self._table = table
        self._op = op
        self._payload = payload
        self.filters: list[tuple[str, str, Any]] = []

    def select(self, *_args: Any) -> _FakeQuery:
        return self

    def eq(self, column: str, value: Any) -> _FakeQuery:
        self.filters.append(("eq", column, value))
        return self

    def is_(self, column: str, value: Any) -> _FakeQuery:
        self.filters.append(("is_", column, value))
        return self

    def limit(self, *_args: Any) -> _FakeQuery:
        return self

    def _matches(self) -> list[dict[str, Any]]:
        results = []
        for row in self._table.rows:
            ok = True
            for kind, column, value in self.filters:
                if kind == "eq" and row.get(column) != value:
                    ok = False
                    break
                if kind == "is_" and row.get(column) is not None:
                    ok = False
                    break
            if ok:
                results.append(row)
        return results

    def execute(self) -> _FakeExecuteResult:
        if self._op == "select":
            matched = self._matches()
            self._table.recorded_selects.append(list(self.filters))
            return _FakeExecuteResult(matched)
        if self._op == "insert":
            payload = self._payload if isinstance(self._payload, list) else [self._payload]
            self._table.rows.extend(dict(row) for row in payload)
            self._table.inserted.extend(payload)
            return _FakeExecuteResult(payload)
        if self._op == "update":
            matched = self._matches()
            for row in matched:
                row.update(self._payload)
            self._table.updated.append((self._payload, list(self.filters)))
            return _FakeExecuteResult(matched)
        if self._op == "delete":
            matched = self._matches()
            for row in matched:
                self._table.rows.remove(row)
            self._table.deleted.append(list(self.filters))
            return _FakeExecuteResult(matched)
        raise AssertionError(f"unexpected op {self._op!r}")  # pragma: no cover


class _FakeTable:
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self.rows: list[dict[str, Any]] = list(rows or [])
        self.inserted: list[Any] = []
        self.updated: list[Any] = []
        self.deleted: list[Any] = []
        self.recorded_selects: list[list[tuple[str, str, Any]]] = []

    def select(self, *_args: Any) -> _FakeQuery:
        return _FakeQuery(self, "select")

    def insert(self, payload: Any) -> _FakeQuery:
        return _FakeQuery(self, "insert", payload)

    def update(self, payload: Any) -> _FakeQuery:
        return _FakeQuery(self, "update", payload)

    def delete(self) -> _FakeQuery:
        return _FakeQuery(self, "delete")


class _FakeSchema:
    def __init__(self) -> None:
        self.tables: dict[str, _FakeTable] = {}

    def table(self, name: str) -> _FakeTable:
        return self.tables.setdefault(name, _FakeTable())


class _FakeClient:
    def __init__(self) -> None:
        self.schemas: dict[str, _FakeSchema] = {}

    def schema(self, name: str) -> _FakeSchema:
        return self.schemas.setdefault(name, _FakeSchema())


BELLEVUE_ID = "aaaaaaaa-0000-0000-0000-000000000001"
UW_ID = "bbbbbbbb-0000-0000-0000-000000000002"
UW_MATH_124_ID = "cccccccc-0000-0000-0000-000000000003"


def _seeded_client() -> _FakeClient:
    client = _FakeClient()
    institutions = client.schema("catalog").table("institutions")
    institutions.rows.extend(
        [
            {"id": BELLEVUE_ID, "slug": "bellevue-college"},
            {"id": UW_ID, "slug": "uw-seattle"},
        ]
    )
    courses = client.schema("catalog").table("courses")
    courses.rows.append(
        {
            "id": UW_MATH_124_ID,
            "institution_id": UW_ID,
            "campus": "Seattle",
            "subject": "MATH",
            "number": "124",
        }
    )
    return client


def _direct_intent() -> EquivalencyIntent:
    return build_equivalency_intents([_DIRECT_RECORD])[0]


def _no_credit_intent() -> EquivalencyIntent:
    return build_equivalency_intents([_NO_CREDIT_RECORD])[0]


def test_publish_missing_institution_raises_clear_error() -> None:
    client = _FakeClient()  # no institutions seeded

    try:
        publish_equivalencies(client, [_direct_intent()])
    except RuntimeError as exc:
        assert "bellevue-college" in str(exc)
    else:
        raise AssertionError("expected RuntimeError for missing institution")


def test_publish_creates_source_course_and_resolves_destination() -> None:
    client = _seeded_client()

    report = publish_equivalencies(client, [_direct_intent()])

    assert report.equivalencies_upserted == 1
    assert report.source_courses_created == 1
    assert report.destinations_resolved == 1
    assert report.destinations_as_category == 0
    assert report.unresolved_destinations == []

    courses = client.schema("catalog").table("courses").rows
    bellevue_course = next(row for row in courses if row["institution_id"] == BELLEVUE_ID)
    assert bellevue_course["subject"] == "MATH&"
    assert bellevue_course["number"] == "151"
    assert bellevue_course["campus"] == "Main"
    assert bellevue_course["active"] is True

    components = client.schema("equivalency").table("equivalency_components").rows
    roles = {c["component_role"] for c in components}
    assert roles == {"source", "destination"}
    destination_component = next(c for c in components if c["component_role"] == "destination")
    assert destination_component["course_id"] == UW_MATH_124_ID


def test_publish_unresolved_destination_becomes_category_never_invents_course() -> None:
    client = _seeded_client()
    record = EquivalencyRecord(
        source_course_codes=["CS 101"],
        mapping_type="direct_equivalent",
        destination_outcome="UW CSE 100",
        credits_awarded=5.0,
    )
    intent = build_equivalency_intents([record])[0]

    report = publish_equivalencies(client, [intent])

    assert report.destinations_resolved == 0
    assert report.destinations_as_category == 1
    assert report.unresolved_destinations == ["UW CSE 100"]

    components = client.schema("equivalency").table("equivalency_components").rows
    category_component = next(c for c in components if c["component_role"] == "category")
    assert category_component["category"] == "UW CSE 100"
    assert category_component.get("course_id") is None


def test_publish_no_credit_records_raw_text_as_category() -> None:
    client = _seeded_client()

    report = publish_equivalencies(client, [_no_credit_intent()])

    assert report.destinations_as_category == 1
    components = client.schema("equivalency").table("equivalency_components").rows
    category_component = next(c for c in components if c["component_role"] == "category")
    assert category_component["category"] == "No credit"


def test_publish_is_idempotent_on_second_run() -> None:
    client = _seeded_client()
    intent = _direct_intent()

    publish_equivalencies(client, [intent])
    first_equivalency_rows = list(client.schema("equivalency").table("course_equivalencies").rows)
    first_component_rows = list(client.schema("equivalency").table("equivalency_components").rows)
    first_course_rows = list(client.schema("catalog").table("courses").rows)

    report_second = publish_equivalencies(client, [intent])

    equivalency_rows = client.schema("equivalency").table("course_equivalencies").rows
    component_rows = client.schema("equivalency").table("equivalency_components").rows
    course_rows = client.schema("catalog").table("courses").rows

    assert len(equivalency_rows) == len(first_equivalency_rows) == 1
    assert len(component_rows) == len(first_component_rows)
    assert len(course_rows) == len(first_course_rows)
    # The existing equivalency row's id is never reassigned across runs.
    assert equivalency_rows[0]["id"] == intent.id
    assert report_second.source_courses_created == 0


def test_publish_creates_course_version_for_new_source_course_with_code_title() -> None:
    client = _seeded_client()

    report = publish_equivalencies(client, [_direct_intent()])

    assert report.source_course_versions_created == 1
    courses = client.schema("catalog").table("courses").rows
    bellevue_course = next(row for row in courses if row["institution_id"] == BELLEVUE_ID)
    versions = client.schema("catalog").table("course_versions").rows
    assert len(versions) == 1
    assert versions[0]["course_id"] == bellevue_course["id"]
    assert versions[0]["title"] == "MATH& 151"


def test_publish_does_not_duplicate_version_when_source_course_already_has_one() -> None:
    client = _seeded_client()
    # Pre-seed the Bellevue course AND its version, mirroring a course that
    # already existed (e.g. from a seed script) before this run.
    key = f"{BELLEVUE_ID}:Main:MATH&:151"
    course_id = str(uuid.uuid5(NAMESPACE, key))
    client.schema("catalog").table("courses").rows.append(
        {
            "id": course_id,
            "institution_id": BELLEVUE_ID,
            "subject": "MATH&",
            "number": "151",
            "campus": "Main",
            "active": True,
        }
    )
    existing_version_id = str(uuid.uuid5(NAMESPACE, f"{course_id}#v"))
    client.schema("catalog").table("course_versions").rows.append(
        {"id": existing_version_id, "course_id": course_id, "title": "MATH& 151"}
    )

    report = publish_equivalencies(client, [_direct_intent()])

    assert report.source_courses_created == 0
    assert report.source_course_versions_created == 0
    versions = client.schema("catalog").table("course_versions").rows
    assert len(versions) == 1
    assert versions[0]["id"] == existing_version_id


def test_publish_deduplicates_shared_source_course_within_one_run() -> None:
    client = _seeded_client()
    record_a = EquivalencyRecord(
        source_course_codes=["CS 101"],
        mapping_type="direct_equivalent",
        destination_outcome="UW CSE 100",
    )
    record_b = EquivalencyRecord(
        source_course_codes=["CS 101"],
        mapping_type="direct_equivalent",
        destination_outcome="No credit",
    )
    intents = build_equivalency_intents([record_a, record_b])

    report = publish_equivalencies(client, intents)

    assert report.source_courses_created == 1
    bellevue_courses = [
        row
        for row in client.schema("catalog").table("courses").rows
        if row["institution_id"] == BELLEVUE_ID
    ]
    assert len(bellevue_courses) == 1
