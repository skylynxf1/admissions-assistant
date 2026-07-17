from __future__ import annotations

import asyncio
import ipaddress
import socket
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, Self
from urllib.parse import urljoin, urlsplit
from uuid import UUID

import httpx

from academic_ingest.config.settings import InstitutionConfig
from academic_ingest.discovery.source_map import AccessPolicy
from academic_ingest.fetching.cache import MemoryValidatorCache
from academic_ingest.fetching.errors import (
    ResponseTooLargeError,
    UnsafeSourceError,
    UnsupportedContentTypeError,
)
from academic_ingest.fetching.rate_limit import AsyncHostRateLimiter

TRANSIENT_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
REDIRECT_STATUS_CODES = frozenset({301, 302, 303, 307, 308})
DEFAULT_ALLOWED_CONTENT_TYPES = frozenset(
    {
        "application/json",
        "application/pdf",
        "application/xml",
        "text/csv",
        "text/html",
        "text/plain",
        "text/xml",
    }
)


class RateLimiter(Protocol):
    async def wait(self, host: str) -> None: ...


class FetchOutcome(StrEnum):
    FETCHED = "fetched"
    NOT_MODIFIED = "not_modified"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True)
class FetchResult:
    crawl_job_id: UUID
    request_url: str
    final_url: str
    outcome: FetchOutcome
    status_code: int | None = None
    content: bytes | None = None
    content_type: str | None = None
    response_headers: dict[str, str] | None = None
    etag: str | None = None
    last_modified: str | None = None
    skip_reason: str | None = None


async def resolve_public_addresses(host: str) -> list[str]:
    loop = asyncio.get_running_loop()
    records = await loop.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    return sorted({str(record[4][0]) for record in records})


class SafeFetchClient:
    def __init__(
        self,
        config: InstitutionConfig,
        *,
        contact_email: str,
        network_enabled: bool = False,
        transport: httpx.AsyncBaseTransport | None = None,
        resolver: Callable[[str], Awaitable[list[str]]] = resolve_public_addresses,
        robots_allowed: Callable[[str], Awaitable[bool]] | None = None,
        rate_limiter: RateLimiter | None = None,
        cache: MemoryValidatorCache | None = None,
        sleeper: Callable[[float], Awaitable[None]] = asyncio.sleep,
        allowed_content_types: frozenset[str] = DEFAULT_ALLOWED_CONTENT_TYPES,
        max_redirects: int = 5,
    ) -> None:
        self.config = config
        self.access_policy = AccessPolicy(config)
        self.network_enabled = network_enabled
        self.resolver = resolver
        self.robots_allowed = robots_allowed
        self.rate_limiter = rate_limiter or AsyncHostRateLimiter(
            config.request_policy.requests_per_second
        )
        self.cache = cache or MemoryValidatorCache()
        self.sleeper = sleeper
        self.allowed_content_types = allowed_content_types
        self.max_redirects = max_redirects
        self._client = httpx.AsyncClient(
            transport=transport,
            follow_redirects=False,
            trust_env=False,
            timeout=config.request_policy.timeout_seconds,
            headers={"User-Agent": config.request_policy.build_user_agent(contact_email)},
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    def validate_url(self, url: str) -> None:
        self.access_policy.require_allowed(url)

    async def _validate_destination(self, url: str) -> str:
        self.validate_url(url)
        host = (urlsplit(url).hostname or "").lower()
        addresses = await self.resolver(host)
        if not addresses:
            raise UnsafeSourceError(f"DNS resolution returned no addresses for {host}")
        for address in addresses:
            try:
                parsed_address = ipaddress.ip_address(address)
            except ValueError as error:
                raise UnsafeSourceError(
                    f"DNS resolver returned an invalid address for {host}: {address}"
                ) from error
            if not parsed_address.is_global:
                raise UnsafeSourceError(
                    f"DNS resolution for {host} reached non-public address {address}"
                )
        return host

    async def fetch(self, url: str, crawl_job_id: UUID) -> FetchResult:
        self.validate_url(url)
        if not self.network_enabled:
            return FetchResult(
                crawl_job_id=crawl_job_id,
                request_url=url,
                final_url=url,
                outcome=FetchOutcome.SKIPPED,
                skip_reason="Network acquisition is disabled; explicit opt-in is required",
            )
        last_response: FetchResult | None = None
        for attempt in range(self.config.request_policy.retries + 1):
            try:
                result = await self._fetch_with_redirects(url, crawl_job_id)
            except httpx.TransportError:
                if attempt >= self.config.request_policy.retries:
                    raise
            else:
                last_response = result
                if result.status_code not in TRANSIENT_STATUS_CODES:
                    return result
                if attempt >= self.config.request_policy.retries:
                    return result
            if self.config.request_policy.exponential_backoff:
                await self.sleeper(float(2**attempt))
        if last_response is not None:
            return last_response
        raise RuntimeError("fetch retry loop terminated without a response")

    async def _fetch_with_redirects(self, url: str, crawl_job_id: UUID) -> FetchResult:
        current_url = url
        for redirect_count in range(self.max_redirects + 1):
            host = await self._validate_destination(current_url)
            if self.robots_allowed is not None and not await self.robots_allowed(current_url):
                return FetchResult(
                    crawl_job_id=crawl_job_id,
                    request_url=url,
                    final_url=current_url,
                    outcome=FetchOutcome.SKIPPED,
                    skip_reason="robots.txt disallows this URL",
                )
            await self.rate_limiter.wait(host)
            headers = self.cache.get(current_url).request_headers()
            request = self._client.build_request("GET", current_url, headers=headers)
            response = await self._client.send(request, stream=True)
            try:
                if response.status_code in REDIRECT_STATUS_CODES:
                    location = response.headers.get("location")
                    if not location:
                        return self._failure_result(url, current_url, crawl_job_id, response)
                    if redirect_count >= self.max_redirects:
                        raise UnsafeSourceError(
                            f"redirect limit of {self.max_redirects} exceeded for {url}"
                        )
                    current_url = urljoin(current_url, location)
                    self.validate_url(current_url)
                    continue
                return await self._read_response(url, current_url, crawl_job_id, response)
            finally:
                await response.aclose()
        raise UnsafeSourceError(f"redirect limit of {self.max_redirects} exceeded for {url}")

    async def _read_response(
        self,
        request_url: str,
        final_url: str,
        crawl_job_id: UUID,
        response: httpx.Response,
    ) -> FetchResult:
        headers = {key: value for key, value in response.headers.items()}
        etag = response.headers.get("etag")
        last_modified = response.headers.get("last-modified")
        if response.status_code == 304:
            return FetchResult(
                crawl_job_id=crawl_job_id,
                request_url=request_url,
                final_url=final_url,
                outcome=FetchOutcome.NOT_MODIFIED,
                status_code=304,
                response_headers=headers,
                etag=etag,
                last_modified=last_modified,
            )
        if response.status_code < 200 or response.status_code >= 300:
            return self._failure_result(request_url, final_url, crawl_job_id, response)
        content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        if content_type not in self.allowed_content_types:
            raise UnsupportedContentTypeError(
                f"content type {content_type or '<missing>'!r} is not allowed"
            )
        maximum = self.config.request_policy.max_response_bytes
        content_length = response.headers.get("content-length")
        if content_length and content_length.isdigit() and int(content_length) > maximum:
            raise ResponseTooLargeError(f"response exceeds configured limit of {maximum} bytes")
        chunks: list[bytes] = []
        size = 0
        async for chunk in response.aiter_bytes():
            size += len(chunk)
            if size > maximum:
                raise ResponseTooLargeError(f"response exceeds configured limit of {maximum} bytes")
            chunks.append(chunk)
        content = b"".join(chunks)
        self.cache.update(final_url, etag=etag, last_modified=last_modified)
        return FetchResult(
            crawl_job_id=crawl_job_id,
            request_url=request_url,
            final_url=final_url,
            outcome=FetchOutcome.FETCHED,
            status_code=response.status_code,
            content=content,
            content_type=content_type,
            response_headers=headers,
            etag=etag,
            last_modified=last_modified,
        )

    @staticmethod
    def _failure_result(
        request_url: str,
        final_url: str,
        crawl_job_id: UUID,
        response: httpx.Response,
    ) -> FetchResult:
        return FetchResult(
            crawl_job_id=crawl_job_id,
            request_url=request_url,
            final_url=final_url,
            outcome=FetchOutcome.FAILED,
            status_code=response.status_code,
            response_headers={key: value for key, value in response.headers.items()},
            skip_reason=f"HTTP {response.status_code}",
        )


__all__ = [
    "FetchOutcome",
    "FetchResult",
    "ResponseTooLargeError",
    "SafeFetchClient",
    "UnsafeSourceError",
    "UnsupportedContentTypeError",
]
