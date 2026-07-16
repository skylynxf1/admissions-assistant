from __future__ import annotations

import posixpath
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from selectolax.parser import HTMLParser

TRACKING_PARAMETERS = {"fbclid", "gclid", "mc_cid", "mc_eid"}


def _normalized_url(url: str) -> str:
    parsed = urlsplit(url)
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower().rstrip(".")
    port = parsed.port
    netloc = host if port in (None, 443) else f"{host}:{port}"
    path = parsed.path or "/"
    trailing_slash = path.endswith("/")
    path = posixpath.normpath(path)
    if not path.startswith("/"):
        path = f"/{path}"
    if trailing_slash and not path.endswith("/"):
        path = f"{path}/"
    query_items = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in TRACKING_PARAMETERS
    ]
    return urlunsplit((scheme, netloc, path, urlencode(sorted(query_items)), ""))


def canonicalize_url(url: str, html: bytes | None) -> str:
    candidate = url
    if html:
        tree = HTMLParser(html)
        for node in tree.css("link[rel][href]"):
            relations = {part.lower() for part in (node.attributes.get("rel") or "").split()}
            if "canonical" in relations:
                candidate = urljoin(url, node.attributes["href"])
                break
    return _normalized_url(candidate)


def discover_links(
    base_url: str,
    html: bytes,
    *,
    allowed_domains: set[str] | frozenset[str],
) -> list[str]:
    tree = HTMLParser(html)
    discovered: set[str] = set()
    for node in tree.css("a[href]"):
        candidate = canonicalize_url(urljoin(base_url, node.attributes["href"]), None)
        parsed = urlsplit(candidate)
        if parsed.scheme == "https" and (parsed.hostname or "").lower() in allowed_domains:
            discovered.add(candidate)
    return sorted(discovered)
