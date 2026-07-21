"""Offline tests for `requirement_publisher.py`.

The pure layer (`build_requirement_intents`) is deterministic and offline-testable per
the brief's TDD section. The executor (`publish_requirements`) does live Supabase I/O;
it is exercised here only against a minimal in-memory fake client (no network),
mirroring the fake-client pattern already used in
`tests/publishing/test_equivalency_publisher.py`.

Records below are trimmed, hand-written stand-ins for the shape of the real UW export
at `.superpowers/sdd/pubdata/uw_reqs.json` (record_type/canonical_key/evidence/payload
only, keeping just the fields `build_requirement_intents` actually reads).
"""

from __future__ import annotations

import uuid
from typing import Any

from academic_ingest.publishing.requirement_publisher import (
    NAMESPACE,
    PublishReport,
    RequirementIntent,
    build_requirement_intents,
    publish_requirements,
)
from academic_ingest.publishing.supabase_publisher import slugify

# ---------------------------------------------------------------------------
# Representative records
# ---------------------------------------------------------------------------

_CS_URL = "https://admit.washington.edu/majors/computer-science/"
_STATS_URL = "https://admit.washington.edu/majors/statistics/"
_UNKNOWN_URL = "https://admit.washington.edu/majors/unknown-major/"

PROGRAM_CS = {
    "record_type": "program",
    "canonical_key": "uw-seattle:computer science",
    "evidence": [{"source_url": _CS_URL}],
    "payload": {"official_name": "Computer Science", "institution_id": "uw-seattle"},
}

PROGRAM_STATS = {
    "record_type": "program",
    "canonical_key": "uw-seattle:statistics",
    "evidence": [{"source_url": _STATS_URL}],
    "payload": {"official_name": "Statistics", "institution_id": "uw-seattle"},
}

REQ_CS_CHOOSE_ONE = {
    "record_type": "requirement",
    "canonical_key": "uw-seattle:cs-prog:major_admission:one of the following courses",
    "evidence": [{"source_url": _CS_URL}],
    "payload": {
        "allowed_courses": ["CSE 123", "CSE 143"],
        "description": "CSE 123 or CSE 143",
        "mandatory": True,
        "minimum_courses": 1,
        "minimum_credits": None,
        "minimum_grade": None,
        "name": "One of the following courses",
        "recommended": False,
        "requirement_type": "major_admission",
    },
}

REQ_STATS_ALL_OF = {
    "record_type": "requirement",
    "canonical_key": "uw-seattle:stats-prog:major_admission:advanced multivariable calculus i",
    "evidence": [{"source_url": _STATS_URL}],
    "payload": {
        "allowed_courses": ["MATH 224"],
        "description": "MATH 224 - Advanced Multivariable Calculus I",
        "mandatory": True,
        "minimum_courses": None,
        "minimum_credits": "5",
        "minimum_grade": "2.0",
        "name": "Advanced Multivariable Calculus I",
        "recommended": False,
        "requirement_type": "major_admission",
    },
}

REQ_UNKNOWN_SOURCE = {
    "record_type": "requirement",
    "canonical_key": "uw-seattle:unknown-prog:major_admission:mystery requirement",
    "evidence": [{"source_url": _UNKNOWN_URL}],
    "payload": {
        "allowed_courses": ["PHIL 100"],
        "description": "Should be skipped: no matching program.",
        "mandatory": True,
        "minimum_courses": None,
        "minimum_credits": None,
        "minimum_grade": None,
        "name": "Mystery requirement",
        "recommended": False,
        "requirement_type": "major_admission",
    },
}

REQ_MANDATORY_AND_RECOMMENDED = {
    "record_type": "requirement",
    "canonical_key": "uw-seattle:cs-prog:major_admission:conflicting flags",
    "evidence": [{"source_url": _CS_URL}],
    "payload": {
        "allowed_courses": ["STAT 220"],
        "description": "Both mandatory and recommended set true in the source export.",
        "mandatory": True,
        "minimum_courses": None,
        "minimum_credits": None,
        "minimum_grade": None,
        "name": "Conflicting flags",
        "recommended": True,
        "requirement_type": "major_admission",
    },
}

_ALL_RECORDS = [
    PROGRAM_CS,
    PROGRAM_STATS,
    REQ_CS_CHOOSE_ONE,
    REQ_STATS_ALL_OF,
    REQ_UNKNOWN_SOURCE,
    REQ_MANDATORY_AND_RECOMMENDED,
]


# ---------------------------------------------------------------------------
# build_requirement_intents: program join by source_url
# ---------------------------------------------------------------------------


def test_join_by_source_url_resolves_program_slug() -> None:
    intents = build_requirement_intents([PROGRAM_CS, REQ_CS_CHOOSE_ONE])

    assert len(intents) == 1
    assert intents[0].program_slug == slugify("Computer Science")


def test_unknown_source_url_is_skipped_and_counted() -> None:
    requirement_records = [REQ_CS_CHOOSE_ONE, REQ_STATS_ALL_OF, REQ_UNKNOWN_SOURCE]
    all_records = [PROGRAM_CS, PROGRAM_STATS, *requirement_records]

    intents = build_requirement_intents(all_records)

    names = {intent.name for intent in intents}
    assert "Mystery requirement" not in names
    # 3 requirement records in, 1 skipped (unknown source_url) -> 2 survive.
    skipped = len(requirement_records) - len(intents)
    assert skipped == 1
    assert len(intents) == 2


# ---------------------------------------------------------------------------
# build_requirement_intents: deterministic ids
# ---------------------------------------------------------------------------


def test_deterministic_ids_stable_across_two_calls() -> None:
    first = build_requirement_intents([PROGRAM_CS, REQ_CS_CHOOSE_ONE])
    second = build_requirement_intents([PROGRAM_CS, REQ_CS_CHOOSE_ONE])

    assert first[0].id == second[0].id
    program_slug = slugify("Computer Science")
    expected_id = str(uuid.uuid5(NAMESPACE, f"{program_slug}|One of the following courses"))
    assert first[0].id == expected_id


# ---------------------------------------------------------------------------
# build_requirement_intents: expression synthesis
# ---------------------------------------------------------------------------


def test_minimum_courses_set_yields_choose_n_expression() -> None:
    intents = build_requirement_intents([PROGRAM_CS, REQ_CS_CHOOSE_ONE])
    expression = intents[0].expression

    assert expression["kind"] == "choose_n"
    assert expression["n"] == 1
    assert expression["courses"] == ["CSE 123", "CSE 143"]
    assert expression["source"] == "uw.major_detail"
    assert "not a parsed expression tree" in expression["note"]


def test_no_minimum_courses_yields_all_of_expression() -> None:
    intents = build_requirement_intents([PROGRAM_STATS, REQ_STATS_ALL_OF])
    expression = intents[0].expression

    assert expression["kind"] == "all_of"
    assert expression["courses"] == ["MATH 224"]
    assert expression["source"] == "uw.major_detail"


# ---------------------------------------------------------------------------
# build_requirement_intents: mandatory/recommended CHECK guard
# ---------------------------------------------------------------------------


def test_mandatory_and_recommended_both_true_is_normalized() -> None:
    intents = build_requirement_intents([PROGRAM_CS, REQ_MANDATORY_AND_RECOMMENDED])

    assert intents[0].mandatory is True
    assert intents[0].recommended is False


# ---------------------------------------------------------------------------
# build_requirement_intents: course code parsing
# ---------------------------------------------------------------------------


def test_allowed_courses_parse_into_subject_number_pairs() -> None:
    intents = build_requirement_intents([PROGRAM_CS, REQ_CS_CHOOSE_ONE])

    assert intents[0].parsed_courses == [("CSE", "123"), ("CSE", "143")]


def test_intent_carries_through_fields() -> None:
    intents = build_requirement_intents([PROGRAM_STATS, REQ_STATS_ALL_OF])
    intent = intents[0]

    assert isinstance(intent, RequirementIntent)
    assert intent.name == "Advanced Multivariable Calculus I"
    assert intent.description == "MATH 224 - Advanced Multivariable Calculus I"
    assert intent.requirement_type == "major_admission"
    assert intent.minimum_courses is None
    assert intent.minimum_credits == 5.0
    assert intent.minimum_grade == "2.0"
    assert intent.mandatory is True
    assert intent.recommended is False
    assert intent.allowed_courses == ["MATH 224"]


# ---------------------------------------------------------------------------
# publish_requirements executor: minimal in-memory fake client (no network)
# ---------------------------------------------------------------------------


class _FakeExecuteResult:
    def __init__(self, data: list[dict[str, Any]]) -> None:
        self.data = data


class _FakeQuery:
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
            return _FakeExecuteResult(self._matches())
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


UW_ID = "aaaaaaaa-0000-0000-0000-000000000001"
CS_PROGRAM_ID = "bbbbbbbb-0000-0000-0000-000000000002"
CSE_123_ID = "cccccccc-0000-0000-0000-000000000003"
CSE_143_ID = "dddddddd-0000-0000-0000-000000000004"


def _seeded_client() -> _FakeClient:
    client = _FakeClient()
    client.schema("catalog").table("institutions").rows.append({"id": UW_ID, "slug": "uw-seattle"})
    client.schema("catalog").table("programs").rows.append(
        {"id": CS_PROGRAM_ID, "institution_id": UW_ID, "slug": slugify("Computer Science")}
    )
    client.schema("catalog").table("courses").rows.extend(
        [
            {"id": CSE_123_ID, "institution_id": UW_ID, "subject": "CSE", "number": "123"},
            {"id": CSE_143_ID, "institution_id": UW_ID, "subject": "CSE", "number": "143"},
        ]
    )
    return client


def _cs_choose_one_intent() -> RequirementIntent:
    return build_requirement_intents([PROGRAM_CS, REQ_CS_CHOOSE_ONE])[0]


def test_publish_missing_institution_raises_clear_error() -> None:
    client = _FakeClient()  # no institutions seeded

    try:
        publish_requirements(client, [_cs_choose_one_intent()])
    except RuntimeError as exc:
        assert "uw-seattle" in str(exc)
    else:
        raise AssertionError("expected RuntimeError for missing institution")


def test_publish_upserts_requirement_and_links_resolved_courses() -> None:
    client = _seeded_client()
    intent = _cs_choose_one_intent()

    report = publish_requirements(client, [intent])

    assert isinstance(report, PublishReport)
    assert report.requirements_upserted == 1
    assert report.requirement_courses_linked == 2
    assert report.programs_missing == []
    assert report.unresolved_courses == []

    requirement_rows = client.schema("policy").table("requirements").rows
    assert len(requirement_rows) == 1
    assert requirement_rows[0]["id"] == intent.id
    assert requirement_rows[0]["program_id"] == CS_PROGRAM_ID
    assert requirement_rows[0]["expression"]["kind"] == "choose_n"

    link_rows = client.schema("policy").table("requirement_courses").rows
    assert {row["course_id"] for row in link_rows} == {CSE_123_ID, CSE_143_ID}
    assert all(row["role"] == "allowed" for row in link_rows)


def test_publish_missing_program_skips_and_records_never_creates_program() -> None:
    client = _seeded_client()
    intent = build_requirement_intents([PROGRAM_STATS, REQ_STATS_ALL_OF])[0]

    report = publish_requirements(client, [intent])

    assert report.requirements_upserted == 0
    assert report.programs_missing == [slugify("Statistics")]
    assert client.schema("policy").table("requirements").rows == []
    # never invents a program row
    program_rows = client.schema("catalog").table("programs").rows
    assert all(row["slug"] != slugify("Statistics") for row in program_rows)


def test_publish_unresolved_course_is_skipped_and_never_invented() -> None:
    client = _seeded_client()
    # MATH 224 does not exist in the seeded courses table.
    intent = build_requirement_intents([PROGRAM_STATS, REQ_STATS_ALL_OF])[0]
    client.schema("catalog").table("programs").rows.append(
        {
            "id": "eeeeeeee-0000-0000-0000-000000000005",
            "institution_id": UW_ID,
            "slug": slugify("Statistics"),
        }
    )

    report = publish_requirements(client, [intent])

    assert report.requirements_upserted == 1
    assert report.requirement_courses_linked == 0
    assert report.unresolved_courses == ["MATH 224"]
    course_rows = client.schema("catalog").table("courses").rows
    assert all(not (row["subject"] == "MATH" and row["number"] == "224") for row in course_rows)


def test_publish_is_idempotent_on_second_run() -> None:
    client = _seeded_client()
    intent = _cs_choose_one_intent()

    publish_requirements(client, [intent])
    first_requirement_rows = list(client.schema("policy").table("requirements").rows)
    first_link_rows = list(client.schema("policy").table("requirement_courses").rows)

    report_second = publish_requirements(client, [intent])

    requirement_rows = client.schema("policy").table("requirements").rows
    link_rows = client.schema("policy").table("requirement_courses").rows

    assert len(requirement_rows) == len(first_requirement_rows) == 1
    assert len(link_rows) == len(first_link_rows) == 2
    assert requirement_rows[0]["id"] == intent.id
    assert report_second.requirements_upserted == 1
