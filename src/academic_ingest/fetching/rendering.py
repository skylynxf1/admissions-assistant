from __future__ import annotations

from typing import Protocol


class RenderingUnavailableError(RuntimeError):
    """Raised when a caller explicitly requests an unconfigured renderer."""


class RenderingStrategy(Protocol):
    async def render(self, url: str) -> bytes: ...


class UnavailableRenderer:
    async def render(self, url: str) -> bytes:
        raise RenderingUnavailableError(
            f"browser rendering is not configured for {url}; no automatic fallback was attempted"
        )
