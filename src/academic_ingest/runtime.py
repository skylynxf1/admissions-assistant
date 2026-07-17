from __future__ import annotations

import asyncio
import selectors
import sys
from collections.abc import Coroutine
from typing import Any


def create_compatible_event_loop() -> asyncio.AbstractEventLoop:
    """Return an event loop compatible with psycopg async connections on Windows."""

    if sys.platform == "win32":
        return asyncio.SelectorEventLoop(selectors.SelectSelector())
    return asyncio.new_event_loop()


def run_sync[ResultT](coroutine: Coroutine[Any, Any, ResultT]) -> ResultT:
    with asyncio.Runner(loop_factory=create_compatible_event_loop) as runner:
        return runner.run(coroutine)
