from __future__ import annotations

from xml.etree import ElementTree

from academic_ingest.discovery.link_discovery import canonicalize_url


class InvalidSitemapError(ValueError):
    """Raised when a sitemap exceeds limits or cannot be parsed safely."""


def parse_sitemap(raw: bytes, *, max_bytes: int = 5 * 1024 * 1024) -> list[str]:
    if len(raw) > max_bytes:
        raise InvalidSitemapError(f"sitemap exceeds {max_bytes} bytes")
    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError as error:
        raise InvalidSitemapError(f"invalid sitemap XML: {error}") from error
    urls: set[str] = set()
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] == "loc" and node.text:
            candidate = node.text.strip()
            if candidate.startswith("https://"):
                urls.add(canonicalize_url(candidate, None))
    return sorted(urls)
