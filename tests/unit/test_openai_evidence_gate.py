from types import SimpleNamespace

from academic_ingest.extraction.openai_client import OpenAIStructuredExtractionClient
from academic_ingest.extraction.schemas.policy import ExtractionContext, ExtractionProposal


class _FakeResponses:
    def __init__(self, proposal: ExtractionProposal) -> None:
        self.proposal = proposal
        self.kwargs = None

    async def parse(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            id="resp_test_123",
            output_parsed=self.proposal,
            usage=SimpleNamespace(model_dump=lambda mode="json": {"input_tokens": 42}),
        )


class _FakeOpenAI:
    def __init__(self, proposal: ExtractionProposal) -> None:
        self.responses = _FakeResponses(proposal)


def _context() -> ExtractionContext:
    return ExtractionContext(
        institution_id="uw-seattle",
        institution_name="University of Washington",
        campus="Seattle",
        canonical_url="https://admit.washington.edu/apply/transfer/policies/",
        page_title="Transfer policies",
        policy_family="transfer_policy",
        cleaned_source_text="A maximum of 90 lower-division credits may transfer.",
        structured_tables=[
            {"heading": "Limits", "headers": ["Level", "Limit"], "rows": [["Lower", "90"]]}
        ],
    )


async def test_openai_client_uses_responses_parse_with_pydantic_schema() -> None:
    proposal = ExtractionProposal(
        proposed_fields={"credit_limit": 90},
        exact_evidence_strings=["maximum of 90 lower-division credits"],
        source_urls=["https://admit.washington.edu/apply/transfer/policies/"],
    )
    sdk = _FakeOpenAI(proposal)
    client = OpenAIStructuredExtractionClient(client=sdk, model="gpt-5.6")

    result = await client.extract_policy(_context())

    assert result.data == proposal
    assert result.metadata.request_id == "resp_test_123"
    assert result.metadata.usage == {"input_tokens": 42}
    assert sdk.responses.kwargs["text_format"] is ExtractionProposal
    assert sdk.responses.kwargs["model"] == "gpt-5.6"
    assert "OPENAI_API_KEY" not in str(sdk.responses.kwargs)


async def test_openai_client_rejects_quote_not_present_in_supplied_content() -> None:
    proposal = ExtractionProposal(
        proposed_fields={"credit_limit": 105},
        exact_evidence_strings=["maximum of 105 lower-division credits"],
    )
    client = OpenAIStructuredExtractionClient(client=_FakeOpenAI(proposal))

    result = await client.extract_policy(_context())

    assert result.data is None
    assert result.metadata.validation_result == "rejected"
    assert result.validation_issues == [
        "evidence_not_found: maximum of 105 lower-division credits"
    ]


async def test_openai_client_rejects_urls_it_was_not_given() -> None:
    proposal = ExtractionProposal(
        proposed_fields={"credit_limit": 90},
        exact_evidence_strings=["maximum of 90 lower-division credits"],
        source_urls=["https://example.com/unsupported"],
    )
    client = OpenAIStructuredExtractionClient(client=_FakeOpenAI(proposal))

    result = await client.extract_policy(_context())

    assert result.data is None
    assert result.validation_issues == ["unsupported_source_url: https://example.com/unsupported"]


async def test_openai_client_bounds_source_text_before_request() -> None:
    proposal = ExtractionProposal(
        proposed_fields={},
        exact_evidence_strings=["policy"],
    )
    sdk = _FakeOpenAI(proposal)
    client = OpenAIStructuredExtractionClient(client=sdk, max_source_chars=100)
    context = _context().model_copy(
        update={"cleaned_source_text": "policy " + ("x" * 500)}
    )

    await client.extract_policy(context)

    request_input = sdk.responses.kwargs["input"]
    assert len(request_input) < 1000
    assert "x" * 200 not in request_input

