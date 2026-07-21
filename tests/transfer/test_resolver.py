"""Tests for the deterministic transfer-outcome resolver.

The resolver must behave identically for every pathway — that sameness is the point,
so every scenario below is parametrized across both configured pathway keys. All
course codes are synthetic (SRC ###) and do not represent real institutional data.
"""

from __future__ import annotations

import pytest

from academic_ingest.models.transfer_state import TransferState
from academic_ingest.pathways.registry import Pathway, UnknownPathwayError
from academic_ingest.transfer.models import EquivalencyRecord, SourceCourseInput
from academic_ingest.transfer.repository import InMemoryEquivalencyRepository
from academic_ingest.transfer.resolver import resolve_outcomes

PATHWAY_KEYS = ["bellevue-college:uw-seattle", "seattle-university:uw-seattle"]

_INSTITUTION_PAIRS = {
    "bellevue-college:uw-seattle": ("bellevue-college", "uw-seattle"),
    "seattle-university:uw-seattle": ("seattle-university", "uw-seattle"),
}

# Explicit pathways fixture to avoid disk I/O in tests.
PATHWAYS = {
    "bellevue-college:uw-seattle": Pathway(
        key="bellevue-college:uw-seattle",
        source_institution_id="bellevue-college",
        destination_institution_id="uw-seattle",
        destination_campus="Seattle",
        capabilities=frozenset({"transfer_outcomes"}),
    ),
    "seattle-university:uw-seattle": Pathway(
        key="seattle-university:uw-seattle",
        source_institution_id="seattle-university",
        destination_institution_id="uw-seattle",
        destination_campus="Seattle",
        capabilities=frozenset({"transfer_outcomes"}),
    ),
}


def _repo_for(pathway_key: str) -> InMemoryEquivalencyRepository:
    source, destination = _INSTITUTION_PAIRS[pathway_key]
    records = [
        EquivalencyRecord(
            source_course_codes=["SRC 101"],
            mapping_type="direct_equivalent",
            destination_outcome="UW TEST 101",
            evidence_refs=["ev-direct"],
        ),
        EquivalencyRecord(
            source_course_codes=["SRC 201", "SRC 202"],
            mapping_type="sequence_equivalent",
            destination_outcome="UW TEST 201",
            evidence_refs=["ev-seq"],
        ),
        EquivalencyRecord(
            source_course_codes=["SRC 301"],
            mapping_type="no_credit",
            destination_outcome="no equivalent credit",
            evidence_refs=["ev-no-credit"],
        ),
        EquivalencyRecord(
            source_course_codes=["SRC 401"],
            mapping_type="direct_equivalent",
            destination_outcome="UW TEST 401",
            evidence_refs=["ev-conflict-a"],
        ),
        EquivalencyRecord(
            source_course_codes=["SRC 401"],
            mapping_type="no_credit",
            destination_outcome="no equivalent credit",
            evidence_refs=["ev-conflict-b"],
        ),
    ]
    return InMemoryEquivalencyRepository({(source, destination): records})


@pytest.mark.parametrize("pathway_key", PATHWAY_KEYS)
class TestResolveOutcomesRunsIdenticallyAcrossPathways:
    def test_direct_record_yields_direct_equivalent(self, pathway_key: str) -> None:
        repo = _repo_for(pathway_key)

        outcomes = resolve_outcomes(
            pathway_key, [SourceCourseInput(code="SRC 101")], repo, pathways=PATHWAYS
        )

        assert outcomes[0].state == TransferState.direct_equivalent
        assert outcomes[0].destination_outcomes == ["UW TEST 101"]
        assert outcomes[0].evidence_refs == ["ev-direct"]

    def test_normalized_code_matches_regardless_of_case_and_spacing(
        self, pathway_key: str
    ) -> None:
        repo = _repo_for(pathway_key)

        outcomes = resolve_outcomes(
            pathway_key, [SourceCourseInput(code="src   101")], repo, pathways=PATHWAYS
        )

        assert outcomes[0].state == TransferState.direct_equivalent

    def test_sequence_with_both_courses_present_yields_sequence_equivalent(
        self, pathway_key: str
    ) -> None:
        repo = _repo_for(pathway_key)
        courses = [SourceCourseInput(code="SRC 201"), SourceCourseInput(code="SRC 202")]

        outcomes = resolve_outcomes(pathway_key, courses, repo, pathways=PATHWAYS)

        assert outcomes[0].state == TransferState.course_sequence_equivalent
        assert outcomes[1].state == TransferState.course_sequence_equivalent
        assert outcomes[0].destination_outcomes == ["UW TEST 201"]

    def test_sequence_with_only_one_course_present_requires_manual_review(
        self, pathway_key: str
    ) -> None:
        repo = _repo_for(pathway_key)

        outcomes = resolve_outcomes(
            pathway_key, [SourceCourseInput(code="SRC 201")], repo, pathways=PATHWAYS
        )

        assert outcomes[0].state == TransferState.manual_review_required
        assert outcomes[0].detail is not None
        assert "SRC 202" in outcomes[0].detail

    def test_unmapped_course_is_not_found_never_explicit_no_credit(
        self, pathway_key: str
    ) -> None:
        repo = _repo_for(pathway_key)

        outcomes = resolve_outcomes(
            pathway_key, [SourceCourseInput(code="SRC 999")], repo, pathways=PATHWAYS
        )

        assert outcomes[0].state == TransferState.not_found
        assert outcomes[0].state != TransferState.explicit_no_credit

    def test_no_credit_record_yields_explicit_no_credit(self, pathway_key: str) -> None:
        repo = _repo_for(pathway_key)

        outcomes = resolve_outcomes(
            pathway_key, [SourceCourseInput(code="SRC 301")], repo, pathways=PATHWAYS
        )

        assert outcomes[0].state == TransferState.explicit_no_credit

    def test_conflicting_records_yield_conflicting_evidence(self, pathway_key: str) -> None:
        repo = _repo_for(pathway_key)

        outcomes = resolve_outcomes(
            pathway_key, [SourceCourseInput(code="SRC 401")], repo, pathways=PATHWAYS
        )

        assert outcomes[0].state == TransferState.conflicting_evidence
        assert set(outcomes[0].evidence_refs) == {"ev-conflict-a", "ev-conflict-b"}
        assert outcomes[0].detail == "Sources disagree"

    def test_order_of_outcomes_matches_order_of_input_courses(self, pathway_key: str) -> None:
        repo = _repo_for(pathway_key)
        courses = [
            SourceCourseInput(code="SRC 999"),
            SourceCourseInput(code="SRC 101"),
            SourceCourseInput(code="SRC 301"),
        ]

        outcomes = resolve_outcomes(pathway_key, courses, repo, pathways=PATHWAYS)

        assert [outcome.state for outcome in outcomes] == [
            TransferState.not_found,
            TransferState.direct_equivalent,
            TransferState.explicit_no_credit,
        ]


    def test_multiple_matching_records_with_same_state_yields_that_state(
        self, pathway_key: str
    ) -> None:
        """Test that multiple records for the same course mapping to the same state
        yield that state (not conflicting). Documents the 'multiple agreeing matches' branch."""
        source, destination = _INSTITUTION_PAIRS[pathway_key]
        records = [
            EquivalencyRecord(
                source_course_codes=["SRC 501"],
                mapping_type="direct_equivalent",
                destination_outcome="UW TEST 501A",
                evidence_refs=["ev-501-a"],
            ),
            EquivalencyRecord(
                source_course_codes=["SRC 501"],
                mapping_type="direct_equivalent",
                destination_outcome="UW TEST 501B",
                evidence_refs=["ev-501-b"],
            ),
        ]
        repo = InMemoryEquivalencyRepository({(source, destination): records})

        outcomes = resolve_outcomes(
            pathway_key, [SourceCourseInput(code="SRC 501")], repo, pathways=PATHWAYS
        )

        assert outcomes[0].state == TransferState.direct_equivalent
        assert outcomes[0].detail is None

    def test_unrecognized_mapping_type_vs_recognized_yields_conflicting_evidence(
        self, pathway_key: str
    ) -> None:
        """Test that one recognized mapping_type and one unrecognized mapping_type
        for the same course yields conflicting_evidence (recognized state vs the
        unrecognized-mapped manual_review_required differ)."""
        source, destination = _INSTITUTION_PAIRS[pathway_key]
        records = [
            EquivalencyRecord(
                source_course_codes=["SRC 601"],
                mapping_type="direct_equivalent",
                destination_outcome="UW TEST 601",
                evidence_refs=["ev-601-recognized"],
            ),
            EquivalencyRecord(
                source_course_codes=["SRC 601"],
                mapping_type="bogus_type",
                destination_outcome="no outcome",
                evidence_refs=["ev-601-bogus"],
            ),
        ]
        repo = InMemoryEquivalencyRepository({(source, destination): records})

        outcomes = resolve_outcomes(
            pathway_key, [SourceCourseInput(code="SRC 601")], repo, pathways=PATHWAYS
        )

        assert outcomes[0].state == TransferState.conflicting_evidence
        assert set(outcomes[0].evidence_refs) == {"ev-601-recognized", "ev-601-bogus"}


def test_unknown_pathway_key_raises_unknown_pathway_error() -> None:
    repo = InMemoryEquivalencyRepository({})

    with pytest.raises(UnknownPathwayError):
        resolve_outcomes(
            "bogus:pathway",
            [SourceCourseInput(code="SRC 101")],
            repo,
            pathways=PATHWAYS,
        )
