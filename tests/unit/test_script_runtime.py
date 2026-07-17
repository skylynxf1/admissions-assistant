import asyncio
import sys

from academic_ingest.runtime import create_compatible_event_loop, run_sync


def test_script_event_loop_is_psycopg_compatible_on_windows() -> None:
    loop = create_compatible_event_loop()
    try:
        if sys.platform == "win32":
            assert isinstance(loop, asyncio.SelectorEventLoop)
    finally:
        loop.close()


def test_run_sync_returns_coroutine_result() -> None:
    async def value() -> int:
        return 42

    assert run_sync(value()) == 42
