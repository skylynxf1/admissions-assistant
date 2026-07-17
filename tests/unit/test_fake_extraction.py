from academic_ingest.extraction.fake_client import FakeStructuredExtractionClient
from academic_ingest.extraction.schemas.policy import ExtractionContext, ExtractionProposal


def _context() -> ExtractionContext:
    return ExtractionContext(
        institution_id="uw-seattle",
        institution_name="University of Washington",
        campus="Seattle",
        canonical_url="https://www.washington.edu/students/crscat/cse.html",
        page_title="Computer Science and Engineering",
        policy_family="course",
        cleaned_source_text="CSE 123 requires CSE 122 with a minimum grade of 2.0.",
        known_deterministic_fields={"course_code": "CSE 123"},
    )


async def test_fake_client_returns_configured_strict_result_and_records_call() -> None:
    proposal = ExtractionProposal(
        proposed_fields={"minimum_grade": "2.0"},
        exact_evidence_strings=["minimum grade of 2.0"],
        unresolved_fields=[],
        ambiguity_warnings=[],
        possible_conflicts=[],
        suggested_review_question=None,
        source_urls=["https://www.washington.edu/students/crscat/cse.html"],
    )
    client = FakeStructuredExtractionClient(results={"extract_policy": proposal})

    result = await client.extract_policy(_context())

    assert result.data == proposal
    assert result.metadata.model_id == "fake-structured-extraction"
    assert result.metadata.validation_result == "accepted"
    assert client.calls[0].operation == "extract_policy"
    assert client.calls[0].context.known_deterministic_fields == {"course_code": "CSE 123"}


async def test_fake_client_uses_the_same_exact_evidence_gate_as_production() -> None:
    proposal = ExtractionProposal(
        proposed_fields={"minimum_grade": "2.5"},
        exact_evidence_strings=["minimum grade of 2.5"],
    )
    client = FakeStructuredExtractionClient(results={"extract_policy": proposal})

    result = await client.extract_policy(_context())

    assert result.metadata.validation_result == "rejected"
    assert result.data is None
    assert result.validation_issues == ["evidence_not_found: minimum grade of 2.5"]


async def test_fake_client_supports_requirement_expression_parsing() -> None:
    proposal = ExtractionProposal(
        proposed_fields={"node_type": "course"},
        exact_evidence_strings=["CSE 122"],
    )
    client = FakeStructuredExtractionClient(
        results={"parse_requirement_expression": proposal}
    )

    result = await client.parse_requirement_expression(_context())

    assert result.data == proposal
    assert client.calls[-1].operation == "parse_requirement_expression"

