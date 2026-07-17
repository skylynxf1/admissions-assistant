from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidatorEntry:
    etag: str | None = None
    last_modified: str | None = None

    def request_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.etag:
            headers["If-None-Match"] = self.etag
        if self.last_modified:
            headers["If-Modified-Since"] = self.last_modified
        return headers


class MemoryValidatorCache:
    def __init__(self) -> None:
        self._entries: dict[str, ValidatorEntry] = {}

    def get(self, url: str) -> ValidatorEntry:
        return self._entries.get(url, ValidatorEntry())

    def update(self, url: str, *, etag: str | None, last_modified: str | None) -> None:
        if etag or last_modified:
            self._entries[url] = ValidatorEntry(etag=etag, last_modified=last_modified)
