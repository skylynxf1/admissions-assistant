"""Deterministic transfer-outcome resolver.

This module is a PURE function over an injected `EquivalencyReadRepository` — it
performs no I/O, no network calls, and no database access. It runs the exact same
code path for every pathway (no per-institution branching); the sameness across
pathways such as `bellevue-college:uw-seattle` and `seattle-university:uw-seattle`
is the whole point.
"""

from __future__ import annotations

from academic_ingest.models.transfer_state import SUPABASE_MAPPING_TYPE_TO_STATE, TransferState
from academic_ingest.pathways.registry import Pathway, get_pathway
from academic_ingest.transfer.models import EquivalencyRecord, SourceCourseInput, TransferOutcome
from academic_ingest.transfer.repository import EquivalencyReadRepository


def _norm(code: str) -> str:
    """Normalize a course code for matching: uppercase, collapse whitespace."""
    return " ".join(code.upper().split())


def _record_state(record: EquivalencyRecord) -> TransferState:
    """The TransferState a record maps to, falling back to manual_review_required
    for mapping_type spellings that aren't in the canonical DB vocabulary."""
    return SUPABASE_MAPPING_TYPE_TO_STATE.get(
        record.mapping_type, TransferState.manual_review_required
    )


def resolve_outcomes(
    pathway_key: str,
    source_courses: list[SourceCourseInput],
    repo: EquivalencyReadRepository,
    pathways: dict[str, Pathway] | None = None,
) -> list[TransferOutcome]:
    """Resolve a transfer outcome for each of `source_courses` along `pathway_key`.

    Raises UnknownPathwayError (propagated from get_pathway) if the pathway key is
    not registered.
    """
    pathway = get_pathway(pathway_key, pathways)
    records = repo.records_for(pathway.source_institution_id, pathway.destination_institution_id)
    all_input_codes = {_norm(course.code) for course in source_courses}

    outcomes: list[TransferOutcome] = []
    for course in source_courses:
        normalized_code = _norm(course.code)
        matches = [
            record
            for record in records
            if normalized_code in {_norm(code) for code in record.source_course_codes}
        ]
        outcomes.append(_resolve_single(course, matches, all_input_codes))
    return outcomes


def _resolve_single(
    course: SourceCourseInput,
    matches: list[EquivalencyRecord],
    all_input_codes: set[str],
) -> TransferOutcome:
    if not matches:
        return TransferOutcome(
            source_course=course,
            state=TransferState.not_found,
            detail="No published equivalency found",
        )

    distinct_states = {_record_state(match) for match in matches}
    if len(distinct_states) > 1:
        evidence_refs = [ref for match in matches for ref in match.evidence_refs]
        return TransferOutcome(
            source_course=course,
            state=TransferState.conflicting_evidence,
            evidence_refs=evidence_refs,
            detail="Sources disagree",
        )

    record = matches[0]
    if record.mapping_type not in SUPABASE_MAPPING_TYPE_TO_STATE:
        return TransferOutcome(
            source_course=course,
            state=TransferState.manual_review_required,
            detail=f"Unrecognized mapping_type {record.mapping_type!r}",
        )

    state = SUPABASE_MAPPING_TYPE_TO_STATE[record.mapping_type]

    if len(record.source_course_codes) > 1:
        missing = [
            code for code in record.source_course_codes if _norm(code) not in all_input_codes
        ]
        if missing:
            return TransferOutcome(
                source_course=course,
                state=TransferState.manual_review_required,
                evidence_refs=record.evidence_refs,
                detail=f"Sequence incomplete: also requires {', '.join(missing)}",
            )

    return TransferOutcome(
        source_course=course,
        state=state,
        destination_outcomes=[record.destination_outcome],
        credits_awarded=record.credits_awarded,
        minimum_grade=record.minimum_grade,
        conditions=record.conditions,
        evidence_refs=record.evidence_refs,
    )
