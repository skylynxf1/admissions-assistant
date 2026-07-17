from __future__ import annotations

import os


def pytest_configure() -> None:
    os.environ.setdefault("ACADEMIC_INGEST_NETWORK_ENABLED", "false")
    os.environ.setdefault("ACADEMIC_INGEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
