from __future__ import annotations

from collections.abc import Iterable

from academic_ingest.adapters.base import AdapterContext, SourceAdapter


class AdapterNotFoundError(LookupError):
    """Raised when no registered deterministic adapter accepts a page."""


class AdapterRegistry:
    def __init__(self, adapters: Iterable[SourceAdapter] = ()) -> None:
        self._adapters: dict[str, SourceAdapter] = {}
        for adapter in adapters:
            self.register(adapter)

    def register(self, adapter: SourceAdapter) -> None:
        if adapter.name in self._adapters:
            raise ValueError(f"duplicate adapter name: {adapter.name}")
        self._adapters[adapter.name] = adapter

    def for_context(self, context: AdapterContext) -> SourceAdapter:
        hinted = self._adapters.get(context.page.adapter_name)
        if hinted is not None and hinted.matches(context.page):
            return hinted
        for adapter in self._adapters.values():
            if adapter.matches(context.page):
                return adapter
        raise AdapterNotFoundError(
            f"no adapter registered for {context.page.adapter_name} ({context.page.url})"
        )
