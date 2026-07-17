from __future__ import annotations

import re

TERM_RE = re.compile(r"^(Autumn|Fall|Winter|Spring|Summer)\s+(\d{4})$", re.IGNORECASE)
TERM_NAMES = {
    "autumn": "autumn",
    "fall": "autumn",
    "winter": "winter",
    "spring": "spring",
    "summer": "summer",
}


def normalize_term(value: str) -> str:
    match = TERM_RE.fullmatch(" ".join(value.split()))
    if match is None:
        raise ValueError(f"unknown academic term format: {value!r}")
    term = TERM_NAMES[match.group(1).lower()]
    return f"{match.group(2)}-{term}"
