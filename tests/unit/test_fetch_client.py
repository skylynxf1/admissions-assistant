from collections.abc import Awaitable, Callable
from uuid import uuid4

import httpx
import pytest

from academic_ingest.config.settings import load_institution_config
from academic_ingest.fetching.client import (
    FetchOutcome,
    ResponseTooLargeError,
    SafeFetchClient,
    UnsafeSourceError,
)


async def public_resolver(_host: str) -> list[str]:
    return ["93.184.216.34"]


async def robots_allow(_url: str) -> bool:
    return True


async def no_sleep(_delay: float) -> None:
    return None


class NoOpRateLimiter:
    async def wait(self, _host: str) -> None:
        return None


def make_client(
    handler: Callable[[httpx.Request], httpx.Response | Awaitable[httpx.Response]],
    *,
    network_enabled: bool = True,
    max_response_bytes: int | None = None,
    resolver: Callable[[str], Awaitable[list[str]]] = public_resolver,
) -> SafeFetchClient:
    config = load_institution_config("config/institutions/uw_seattle.yaml")
    if max_response_bytes is not None:
        config.request_policy.max_response_bytes = max_response_bytes
    return SafeFetchClient(
        config,
        contact_email="operator@example.edu",
        network_enabled=network_enabled,
        transport=httpx.MockTransport(handler),
        resolver=resolver,
        robots_allowed=robots_allow,
        rate_limiter=NoOpRateLimiter(),
        sleeper=no_sleep,
    )


def test_fetch_rejects_disallowed_host() -> None:
    client = make_client(lambda _request: httpx.Response(200))

    with pytest.raises(UnsafeSourceError, match="allowlisted"):
        client.validate_url("https://example.com/policy")


async def test_fetch_retries_only_transient_responses() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503, request=request)
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8", "etag": '"v1"'},
            content=b"official policy",
            request=request,
        )

    async with make_client(handler) as client:
        result = await client.fetch("https://www.washington.edu/students/crscat/", uuid4())

    assert attempts == 2
    assert result.outcome is FetchOutcome.FETCHED
    assert result.content == b"official policy"
    assert result.etag == '"v1"'


async def test_fetch_validates_redirect_target_before_following() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            302,
            headers={"location": "https://127.0.0.1/private"},
            request=request,
        )

    async with make_client(handler) as client:
        with pytest.raises(UnsafeSourceError, match="IP-literal"):
            await client.fetch("https://www.washington.edu/start", uuid4())


async def test_fetch_caps_streamed_response_bytes() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            content=b"12345",
            request=request,
        )

    async with make_client(handler, max_response_bytes=4) as client:
        with pytest.raises(ResponseTooLargeError, match="4"):
            await client.fetch("https://www.washington.edu/policy", uuid4())


async def test_fetch_is_explicitly_disabled_by_default() -> None:
    client = make_client(lambda _request: httpx.Response(200), network_enabled=False)

    async with client:
        result = await client.fetch("https://www.washington.edu/policy", uuid4())

    assert result.outcome is FetchOutcome.SKIPPED
    assert "disabled" in (result.skip_reason or "").lower()


async def test_fetch_rejects_private_dns_resolution() -> None:
    async def private_resolver(_host: str) -> list[str]:
        return ["10.0.0.7"]

    async with make_client(
        lambda _request: httpx.Response(200), resolver=private_resolver
    ) as client:
        with pytest.raises(UnsafeSourceError, match="non-public"):
            await client.fetch("https://www.washington.edu/policy", uuid4())


async def test_fetch_uses_etag_for_conditional_revalidation() -> None:
    seen_if_none_match: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        validator = request.headers.get("if-none-match")
        seen_if_none_match.append(validator)
        if validator == '"v1"':
            return httpx.Response(304, request=request)
        return httpx.Response(
            200,
            headers={"content-type": "text/html", "etag": '"v1"'},
            content=b"unchanged",
            request=request,
        )

    async with make_client(handler) as client:
        first = await client.fetch("https://www.washington.edu/policy", uuid4())
        second = await client.fetch("https://www.washington.edu/policy", uuid4())

    assert first.outcome is FetchOutcome.FETCHED
    assert second.outcome is FetchOutcome.NOT_MODIFIED
    assert seen_if_none_match == [None, '"v1"']
