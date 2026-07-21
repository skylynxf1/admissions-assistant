"""Canonical transfer-state vocabulary shared across all transfer logic."""

from enum import StrEnum


class TransferState(StrEnum):
    """The single canonical enum for transfer course evaluation outcomes."""

    direct_equivalent = "direct_equivalent"
    course_sequence_equivalent = "course_sequence_equivalent"
    elective_or_general_credit = "elective_or_general_credit"
    transferable_no_direct_equivalent = "transferable_no_direct_equivalent"
    explicit_no_credit = "explicit_no_credit"
    not_found = "not_found"
    conflicting_evidence = "conflicting_evidence"
    manual_review_required = "manual_review_required"
    cannot_determine = "cannot_determine"


# Map every value of the DB equivalency.mapping_type enum to a TransferState.
SUPABASE_MAPPING_TYPE_TO_STATE: dict[str, TransferState] = {
    "direct_equivalent": TransferState.direct_equivalent,
    "departmental_elective": TransferState.elective_or_general_credit,
    "general_elective": TransferState.elective_or_general_credit,
    "general_education": TransferState.elective_or_general_credit,
    "major_requirement": TransferState.transferable_no_direct_equivalent,
    "sequence_equivalent": TransferState.course_sequence_equivalent,
    "partial_equivalent": TransferState.course_sequence_equivalent,
    "no_credit": TransferState.explicit_no_credit,
    "not_found": TransferState.not_found,
    "manual_review": TransferState.manual_review_required,
}

# Inverse mapping: single DB spelling for each state (where one exists).
STATE_TO_SUPABASE_MAPPING_TYPE: dict[TransferState, str] = {
    TransferState.direct_equivalent: "direct_equivalent",
    TransferState.course_sequence_equivalent: "sequence_equivalent",
    TransferState.elective_or_general_credit: "general_elective",
    TransferState.transferable_no_direct_equivalent: "major_requirement",
    TransferState.explicit_no_credit: "no_credit",
    TransferState.not_found: "not_found",
    TransferState.manual_review_required: "manual_review",
    # conflicting_evidence and cannot_determine have no DB spelling
}
