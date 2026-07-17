from pathlib import Path
from uuid import uuid4

from academic_ingest.adapters.base import AdapterContext
from academic_ingest.adapters.uw.transfer_admissions import TransferAdmissionsAdapter
from academic_ingest.adapters.uw.transfer_policies import TransferPolicyAdapter
from academic_ingest.classification.page_classifier import PageClassifier
from academic_ingest.models.enums import MappingOutcome


def context(fixture: str, url: str) -> AdapterContext:
    html = Path(f"tests/fixtures/uw/html/{fixture}").read_bytes()
    return AdapterContext(
        page=PageClassifier().classify(url, html, content_type="text/html"),
        raw_content=html,
        source_snapshot_id=uuid4(),
        crawl_job_id=uuid4(),
        institution_id="uw-seattle",
        campus="Seattle",
    )


def test_transfer_table_retains_headers_and_footnote() -> None:
    result = TransferPolicyAdapter().extract(
        context(
            "transfer_policies.html",
            "https://admit.washington.edu/apply/transfer/policies/",
        )
    )
    rule = next(item for item in result.records if item.policy_type == "lower_division_limit")

    assert rule.credit_limit == 90
    assert rule.evidence[0].heading_context == "Transfer credit limits"
    assert (
        "Credit source | Maximum quarter credits | Degree applicability"
        in rule.evidence[0].evidence_text
    )
    assert rule.evidence[0].footnote_context == "Limit applies toward the degree total."
    assert rule.evidence[0].table_identifier == "credit-limit-table"
    assert rule.evidence[0].row_identifier == "lower-division"


def test_transfer_admission_rows_are_separate_scoped_rules() -> None:
    result = TransferAdmissionsAdapter().extract(
        context(
            "transfer_admissions.html",
            "https://admit.washington.edu/apply/transfer/",
        )
    )
    deadlines = [item for item in result.records if item.rule_type == "application_deadline"]

    assert [item.timing for item in deadlines] == ["Winter*", "Autumn", "Spring**"]
    assert deadlines[0].conditions["application_deadline"] == "September 1"
    assert (
        "Winter is open to U.S. transfer applicants only"
        in deadlines[0].evidence[0].footnote_context
    )
    assert any(item.rule_type == "applicant_definition" for item in result.records)


def test_explicit_no_credit_is_never_derived_from_missing_mapping() -> None:
    result = TransferPolicyAdapter().extract(
        context(
            "transfer_policies.html",
            "https://admit.washington.edu/apply/transfer/policies/",
        )
    )
    no_credit = [
        item
        for item in result.records
        if item.conditions.get("mapping_outcome") == MappingOutcome.EXPLICIT_NO_CREDIT.value
    ]

    assert len(no_credit) == 2
    assert all("receive no credit" in item.evidence[0].evidence_text for item in no_credit)
    assert all("No mapping was found" not in item.evidence[0].evidence_text for item in no_credit)


def test_dta_scope_does_not_claim_guaranteed_admission() -> None:
    result = TransferPolicyAdapter().extract(
        context(
            "transfer_policies.html",
            "https://admit.washington.edu/apply/transfer/policies/",
        )
    )
    dta = next(item for item in result.records if item.policy_type == "direct_transfer_agreement")

    assert dta.conditions["admission_agreement"] is False
    assert dta.class_standing_effect == "Junior standing upon admission"
