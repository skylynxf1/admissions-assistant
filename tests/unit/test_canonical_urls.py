from academic_ingest.discovery.link_discovery import canonicalize_url, discover_links


def test_html_canonical_wins_and_tracking_parameters_are_removed() -> None:
    html = b'<html><head><link rel="canonical" href="/apply/transfer/?utm_source=x"></head></html>'

    canonical = canonicalize_url(
        "https://ADMIT.washington.edu/apply/transfer/index.html#deadlines",
        html,
    )

    assert canonical == "https://admit.washington.edu/apply/transfer/"


def test_significant_query_parameters_are_sorted() -> None:
    canonical = canonicalize_url(
        "https://www.washington.edu/policy?b=2&utm_medium=email&a=1#top",
        None,
    )

    assert canonical == "https://www.washington.edu/policy?a=1&b=2"


def test_link_discovery_deduplicates_and_applies_scope() -> None:
    html = b"""
    <a href="/students/crscat/cse.html#courses">CSE</a>
    <a href="https://example.com/offsite">Offsite</a>
    <a href="/students/crscat/cse.html">Duplicate</a>
    """

    links = discover_links(
        "https://www.washington.edu/students/crscat/",
        html,
        allowed_domains={"www.washington.edu"},
    )

    assert links == ["https://www.washington.edu/students/crscat/cse.html"]
