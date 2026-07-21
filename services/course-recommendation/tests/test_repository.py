from __future__ import annotations

from typing import Any

from app.repository import SupabaseRecommendationRepository


class FakeResult:
    def __init__(self, data: list[dict[str, Any]]) -> None:
        self.data = data


class FakeQuery:
    """Mimics the small slice of the supabase-py query builder the repository uses."""

    def __init__(self, rows: list[dict[str, Any]], calls: list[tuple]) -> None:
        self._source_rows = rows
        self._rows = rows
        self._calls = calls

    def in_(self, column: str, ids: list[str]) -> FakeQuery:
        self._calls.append(("in_", column, list(ids)))
        ids_set = set(ids)
        self._rows = [row for row in self._source_rows if row.get(column) in ids_set]
        return self

    def range(self, start: int, end: int) -> FakeQuery:
        self._calls.append(("range", start, end))
        self._rows = self._source_rows[start : end + 1]
        return self

    def execute(self) -> FakeResult:
        return FakeResult(self._rows)


class FakeTable:
    def __init__(self, rows: list[dict[str, Any]], calls: list[tuple]) -> None:
        self._rows = rows
        self._calls = calls

    def select(self, columns: str) -> FakeQuery:
        self._calls.append(("select", columns))
        return FakeQuery(self._rows, self._calls)


class FakeSchema:
    def __init__(self, tables: dict[str, list[dict[str, Any]]], calls: list[tuple]) -> None:
        self._tables = tables
        self._calls = calls

    def table(self, name: str) -> FakeTable:
        return FakeTable(self._tables.get(name, []), self._calls)


class FakeClient:
    def __init__(self, tables: dict[str, list[dict[str, Any]]]) -> None:
        self._tables = tables
        self.calls: list[tuple] = []

    def schema(self, name: str) -> FakeSchema:
        del name
        return FakeSchema(self._tables, self.calls)


def repository_for(table: str, rows: list[dict[str, Any]]) -> SupabaseRecommendationRepository:
    return SupabaseRecommendationRepository(FakeClient({table: rows}))


# ---------------------------------------------------------------------------
# _select_in_chunks
# ---------------------------------------------------------------------------


def test_select_in_chunks_returns_empty_and_skips_query_for_empty_id_list():
    repository = repository_for("course_offerings", [{"id": "a", "course_id": "c1"}])

    rows = repository._select_in_chunks("catalog", "course_offerings", "course_id", [])

    assert rows == []
    assert repository.client.calls == []


def test_select_in_chunks_single_chunk_when_ids_fit_in_one_request():
    catalog_rows = [
        {"id": "off-1", "course_id": "c1"},
        {"id": "off-2", "course_id": "c2"},
        {"id": "off-3", "course_id": "c3"},
    ]
    repository = repository_for("course_offerings", catalog_rows)

    rows = repository._select_in_chunks(
        "catalog", "course_offerings", "course_id", ["c1", "c2"], chunk_size=150
    )

    assert [row["id"] for row in rows] == ["off-1", "off-2"]
    in_calls = [call for call in repository.client.calls if call[0] == "in_"]
    assert len(in_calls) == 1


def test_select_in_chunks_splits_across_multiple_requests_and_concatenates_results():
    catalog_rows = [{"id": f"off-{i}", "course_id": f"c{i}"} for i in range(5)]
    repository = repository_for("course_offerings", catalog_rows)
    ids = [f"c{i}" for i in range(5)]

    rows = repository._select_in_chunks(
        "catalog", "course_offerings", "course_id", ids, chunk_size=2
    )

    assert [row["id"] for row in rows] == ["off-0", "off-1", "off-2", "off-3", "off-4"]
    in_calls = [call for call in repository.client.calls if call[0] == "in_"]
    assert len(in_calls) == 3
    assert [call[2] for call in in_calls] == [["c0", "c1"], ["c2", "c3"], ["c4"]]


# ---------------------------------------------------------------------------
# _select_all_paged
# ---------------------------------------------------------------------------


def test_select_all_paged_single_short_page():
    rows_data = [{"id": "1"}, {"id": "2"}]
    repository = repository_for("recommendation_courses", rows_data)

    rows = repository._select_all_paged("catalog", "recommendation_courses", page_size=5)

    assert [row["id"] for row in rows] == ["1", "2"]
    range_calls = [call for call in repository.client.calls if call[0] == "range"]
    assert range_calls == [("range", 0, 4)]


def test_select_all_paged_stops_after_short_page_following_exact_multiple():
    rows_data = [{"id": str(i)} for i in range(6)]
    repository = repository_for("recommendation_courses", rows_data)

    rows = repository._select_all_paged("catalog", "recommendation_courses", page_size=3)

    assert [row["id"] for row in rows] == [str(i) for i in range(6)]
    range_calls = [call for call in repository.client.calls if call[0] == "range"]
    assert range_calls == [("range", 0, 2), ("range", 3, 5), ("range", 6, 8)]


def test_select_all_paged_multiple_pages_with_trailing_partial_page():
    rows_data = [{"id": str(i)} for i in range(7)]
    repository = repository_for("recommendation_courses", rows_data)

    rows = repository._select_all_paged("catalog", "recommendation_courses", page_size=3)

    assert [row["id"] for row in rows] == [str(i) for i in range(7)]
    range_calls = [call for call in repository.client.calls if call[0] == "range"]
    assert range_calls == [("range", 0, 2), ("range", 3, 5), ("range", 6, 8)]
