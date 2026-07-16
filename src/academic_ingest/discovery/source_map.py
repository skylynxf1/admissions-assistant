from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from urllib.parse import urlsplit

from academic_ingest.config.settings import InstitutionConfig
from academic_ingest.fetching.errors import UnsafeSourceError


@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    reason: str


@dataclass(frozen=True)
class SourceMapEntry:
    url: str
    adapter: str
    policy_family: str
    authority: str
    campus: str
    conditional: bool = False


class AccessPolicy:
    def __init__(self, config: InstitutionConfig) -> None:
        self.config = config
        self.allowed_domains = frozenset(config.allowed_domains)

    def evaluate(self, url: str) -> AccessDecision:
        if any(ord(character) < 32 for character in url):
            return AccessDecision(False, "URL contains control characters")
        try:
            parsed = urlsplit(url)
            port = parsed.port
        except ValueError as error:
            return AccessDecision(False, f"URL is malformed: {error}")
        if parsed.scheme.lower() != "https":
            return AccessDecision(False, "Only HTTPS source URLs are permitted")
        if parsed.username is not None or parsed.password is not None:
            return AccessDecision(False, "Embedded URL credentials are prohibited")
        if port not in (None, 443):
            return AccessDecision(False, "Only the standard HTTPS port is permitted")
        host = (parsed.hostname or "").lower().rstrip(".")
        if not host:
            return AccessDecision(False, "URL must include a hostname")
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            return AccessDecision(False, "IP-literal source URLs are prohibited")
        if host not in self.allowed_domains:
            return AccessDecision(False, f"Host {host!r} is not explicitly allowlisted")
        if self.config.url_belongs_to_disallowed_campus(url):
            return AccessDecision(False, "URL matches a disallowed campus scope")
        return AccessDecision(True, "Official HTTPS source is within configured scope")

    def require_allowed(self, url: str) -> None:
        decision = self.evaluate(url)
        if not decision.allowed:
            raise UnsafeSourceError(decision.reason)
