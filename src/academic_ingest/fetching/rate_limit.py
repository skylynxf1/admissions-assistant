from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from time import monotonic


class AsyncHostRateLimiter:
    def __init__(
        self,
        requests_per_second: float,
        *,
        clock: Callable[[], float] = monotonic,
        sleeper: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")
        self.interval = 1 / requests_per_second
        self.clock = clock
        self.sleeper = sleeper
        self._last_request: dict[str, float] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._locks_guard = asyncio.Lock()

    async def wait(self, host: str) -> None:
        async with self._locks_guard:
            lock = self._locks.setdefault(host, asyncio.Lock())
        async with lock:
            previous = self._last_request.get(host)
            if previous is not None:
                delay = self.interval - (self.clock() - previous)
                if delay > 0:
                    await self.sleeper(delay)
            self._last_request[host] = self.clock()
