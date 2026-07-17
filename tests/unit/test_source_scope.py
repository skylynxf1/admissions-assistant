import pytest

from academic_ingest.config.settings import load_institution_config
from academic_ingest.discovery.source_map import AccessPolicy
from academic_ingest.fetching.client import UnsafeSourceError


@pytest.fixture
def access_policy() -> AccessPolicy:
    config = load_institution_config("config/institutions/uw_seattle.yaml")
    return AccessPolicy(config)


@pytest.mark.parametrize(
    ("url", "message"),
    [
        ("http://www.washington.edu/policy", "HTTPS"),
        ("https://example.com/policy", "allowlisted"),
        ("https://user:pass@www.washington.edu/policy", "credentials"),
        ("https://127.0.0.1/policy", "IP-literal"),
        ("https://www.washington.edu/tacoma/catalog", "campus"),
    ],
)
def test_access_policy_rejects_unsafe_sources(
    access_policy: AccessPolicy, url: str, message: str
) -> None:
    decision = access_policy.evaluate(url)

    assert decision.allowed is False
    assert message.lower() in decision.reason.lower()
    with pytest.raises(UnsafeSourceError, match=message):
        access_policy.require_allowed(url)


def test_access_policy_accepts_configured_official_host(access_policy: AccessPolicy) -> None:
    decision = access_policy.evaluate("https://www.washington.edu/students/crscat/cse.html")

    assert decision.allowed is True
