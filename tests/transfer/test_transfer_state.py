"""Test suite for transfer state vocabulary."""

from src.academic_ingest.models.transfer_state import (
    STATE_TO_SUPABASE_MAPPING_TYPE,
    SUPABASE_MAPPING_TYPE_TO_STATE,
    TransferState,
)


class TestTransferStateEnum:
    """Verify TransferState enum has the correct members."""

    def test_transfer_state_has_all_nine_members(self):
        """Assert all 9 TransferState members exist."""
        expected_members = {
            "direct_equivalent",
            "course_sequence_equivalent",
            "elective_or_general_credit",
            "transferable_no_direct_equivalent",
            "explicit_no_credit",
            "not_found",
            "conflicting_evidence",
            "manual_review_required",
            "cannot_determine",
        }
        actual_members = {member.name for member in TransferState}
        assert actual_members == expected_members

    def test_transfer_state_names_match_values(self):
        """Assert name == value for every member."""
        for member in TransferState:
            assert member.name == member.value


class TestSupabaseMapping:
    """Verify mappings between DB enum and TransferState."""

    def test_no_credit_maps_to_explicit_no_credit(self):
        """Assert DB 'no_credit' maps to TransferState.explicit_no_credit."""
        assert SUPABASE_MAPPING_TYPE_TO_STATE["no_credit"] is TransferState.explicit_no_credit

    def test_not_found_maps_to_not_found(self):
        """Assert DB 'not_found' maps to TransferState.not_found."""
        assert SUPABASE_MAPPING_TYPE_TO_STATE["not_found"] is TransferState.not_found

    def test_direct_equivalent_maps_to_direct_equivalent(self):
        """Assert DB 'direct_equivalent' maps to TransferState.direct_equivalent."""
        assert (
            SUPABASE_MAPPING_TYPE_TO_STATE["direct_equivalent"]
            is TransferState.direct_equivalent
        )

    def test_all_db_enum_values_are_mapped(self):
        """Assert every DB enum value is a key in SUPABASE_MAPPING_TYPE_TO_STATE."""
        db_enum_values = {
            "direct_equivalent",
            "departmental_elective",
            "general_elective",
            "general_education",
            "major_requirement",
            "sequence_equivalent",
            "partial_equivalent",
            "no_credit",
            "not_found",
            "manual_review",
        }
        for db_value in db_enum_values:
            assert (
                db_value in SUPABASE_MAPPING_TYPE_TO_STATE
            ), f"Missing mapping for DB value: {db_value}"

    def test_forward_and_inverse_mappings_are_consistent(self):
        """Assert forward and inverse mappings are consistent where both exist."""
        for state, db_spelling in STATE_TO_SUPABASE_MAPPING_TYPE.items():
            assert SUPABASE_MAPPING_TYPE_TO_STATE[db_spelling] is state, (
                f"Inconsistent mapping: {state.value} -> {db_spelling}, "
                f"but {db_spelling} -> {SUPABASE_MAPPING_TYPE_TO_STATE[db_spelling].value}"
            )
