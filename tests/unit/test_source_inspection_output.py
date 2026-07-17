from scripts.inspect_uw_sources import inspect_sources


def test_inspection_requires_explicit_network_permission() -> None:
    results = inspect_sources(
        ["https://www.washington.edu/students/crscat/"],
        allow_network=False,
    )

    assert len(results) == 1
    assert results[0].outcome == "skipped"
    assert results[0].warnings == ["network_disabled"]
    assert results[0].content_size_bytes is None


def test_disabled_inspection_does_not_validate_dns_or_require_contact_email() -> None:
    result = inspect_sources(
        ["https://example.com/not-an-allowed-source"],
        allow_network=False,
    )[0]

    assert result.warnings == ["network_disabled"]
    assert result.final_url is None
