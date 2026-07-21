"""Tests for the bundled-guide loader that replaces hand-curation as the source of
Bellevue College -> UW Seattle equivalency data.

`load_bellevue_guide_records()` must read the guide HTML bundled as package data
(via `importlib.resources`, never a CWD-relative path) and parse it with
`parse_bellevue_equivalencies`. These tests run entirely offline.
"""

from __future__ import annotations

from academic_ingest.transfer import guide_source
from academic_ingest.transfer.guide_source import load_bellevue_guide_records


def test_returns_more_than_300_records() -> None:
    records = load_bellevue_guide_records()
    assert len(records) > 300


def test_every_record_has_source_codes_and_evidence() -> None:
    records = load_bellevue_guide_records()
    assert records, "expected at least one record to check"
    for record in records:
        assert record.source_course_codes
        assert record.evidence_refs


def test_repeated_calls_are_cached_and_parse_only_once(monkeypatch) -> None:
    call_count = 0
    original_parse = guide_source.parse_bellevue_equivalencies

    def counting_parse(*args: object, **kwargs: object):
        nonlocal call_count
        call_count += 1
        return original_parse(*args, **kwargs)  # type: ignore[arg-type]

    # Force a fresh parse so this test doesn't just observe a cache warmed by an
    # earlier test in the same process.
    guide_source._load_result.cache_clear()
    monkeypatch.setattr(guide_source, "parse_bellevue_equivalencies", counting_parse)

    first = load_bellevue_guide_records()
    second = load_bellevue_guide_records()

    assert call_count == 1, "the guide must be parsed once and cached, not per call"
    assert first is second
