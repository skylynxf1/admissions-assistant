"""Loads the bundled UW Bellevue College equivalency guide as `EquivalencyRecord`s.

This REPLACES the now-deleted `curated_equivalencies` module (hand-transcribed, 15
records) as the source the `/transfer/outcomes` endpoint and the equivalency
publisher CLI both read from. The guide HTML is bundled as package data
(`academic_ingest/data/equivalency_guide_bellevue.html`) and loaded via
`importlib.resources` — never a CWD-relative filesystem path — so it works
regardless of the process's working directory, with no database and no network.

The guide is ~416 KB and `parse_bellevue_equivalencies` walks every row of it, so
the parse result is cached at module level (`functools.lru_cache`): the file is
parsed once per process, not once per request.
"""

from __future__ import annotations

from functools import lru_cache
from importlib import resources

from academic_ingest.adapters.uw.bellevue_equivalency import (
    ParseResult,
    parse_bellevue_equivalencies,
)
from academic_ingest.transfer.models import EquivalencyRecord

BELLEVUE_GUIDE_URL = "https://admit.washington.edu/apply/transfer/equivalency-guide/bellevue/"

_GUIDE_PACKAGE = "academic_ingest.data"
_GUIDE_FILENAME = "equivalency_guide_bellevue.html"


@lru_cache(maxsize=1)
def _load_result() -> ParseResult:
    html = resources.files(_GUIDE_PACKAGE).joinpath(_GUIDE_FILENAME).read_text(encoding="utf-8")
    return parse_bellevue_equivalencies(html, source_url=BELLEVUE_GUIDE_URL)


def load_bellevue_guide_records() -> list[EquivalencyRecord]:
    """Return the parsed Bellevue College -> UW Seattle equivalency records.

    Parses the bundled guide snapshot once per process (cached); repeated calls
    return the same list object.
    """
    return _load_result().records
