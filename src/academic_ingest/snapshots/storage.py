from __future__ import annotations

import os
import re
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from academic_ingest.snapshots.hashing import normalized_hash, raw_hash

SAFE_SUFFIX = re.compile(r"^[a-z0-9]{1,12}$")


@dataclass(frozen=True)
class StoredSnapshot:
    path: Path
    location: str
    raw_content_hash: str
    normalized_content_hash: str
    size_bytes: int


class SnapshotStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def put(self, raw: bytes, *, suffix: str) -> StoredSnapshot:
        normalized_suffix = suffix.lower().lstrip(".")
        if not SAFE_SUFFIX.fullmatch(normalized_suffix):
            raise ValueError(f"unsafe snapshot suffix: {suffix!r}")
        content_hash = raw_hash(raw)
        directory = self.root / content_hash[:2]
        path = directory / f"{content_hash}.{normalized_suffix}"
        directory.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            temporary_path = directory / f".{content_hash}.{uuid4().hex}.tmp"
            try:
                with temporary_path.open("xb") as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                with suppress(FileExistsError):
                    temporary_path.replace(path)
            finally:
                temporary_path.unlink(missing_ok=True)
        return StoredSnapshot(
            path=path,
            location=path.resolve().as_uri(),
            raw_content_hash=content_hash,
            normalized_content_hash=normalized_hash(raw),
            size_bytes=len(raw),
        )
