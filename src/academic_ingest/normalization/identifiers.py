from __future__ import annotations

import re

COURSE_CODE_RE = re.compile(r"^(?P<subject>[A-Za-z][A-Za-z &]*?)\s+(?P<number>\d{3}[A-Za-z]?)$")


def normalize_whitespace(value: str) -> str:
    return " ".join(value.split())


def normalize_course_code(value: str) -> tuple[str, str, str]:
    normalized = normalize_whitespace(value)
    match = COURSE_CODE_RE.fullmatch(normalized)
    if match is None:
        raise ValueError(f"unknown course identifier format: {value!r}")
    subject = normalize_whitespace(match.group("subject")).upper()
    number = match.group("number").upper()
    return subject, number, f"{subject} {number}"


def normalize_institution_id(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not normalized:
        raise ValueError("institution identifier cannot be empty")
    return normalized
