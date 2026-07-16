from academic_ingest.fetching.rate_limit import AsyncHostRateLimiter


async def test_rate_limiter_spaces_requests_per_host() -> None:
    now = 100.0
    sleeps: list[float] = []

    def clock() -> float:
        return now

    async def sleep(delay: float) -> None:
        nonlocal now
        sleeps.append(delay)
        now += delay

    limiter = AsyncHostRateLimiter(2, clock=clock, sleeper=sleep)

    await limiter.wait("www.washington.edu")
    await limiter.wait("www.washington.edu")
    await limiter.wait("admit.washington.edu")

    assert sleeps == [0.5]
