from academic_ingest.adapters.registry import AdapterRegistry
from academic_ingest.adapters.uw.ap_credit import APCreditAdapter
from tests.unit.test_uw_ap_credit import ap_context


def test_ap_fixture_flows_through_registry_with_evidence() -> None:
    context = ap_context()
    result = AdapterRegistry([APCreditAdapter()]).for_context(context).extract(context)

    assert len(result.records) == 5
    assert all(record.evidence[0].table_identifier.startswith("ap-") for record in result.records)
    assert all(record.evidence[0].heading_context for record in result.records)
