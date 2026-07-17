from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select

from academic_ingest.api.serialization import evidence_for_version, serialize_model
from academic_ingest.config.settings import Settings
from academic_ingest.db.models import (
    ConflictRecordModel,
    RecordVersionModel,
    ReviewTaskModel,
    SourcePageModel,
    SourceSnapshotModel,
)
from academic_ingest.db.session import create_engine_and_session
from academic_ingest.runtime import run_sync


async def _export_records(database_url: str) -> dict[str, Any]:
    engine, session_factory = create_engine_and_session(database_url)
    try:
        async with session_factory() as session:
            versions = list(
                await session.scalars(
                    select(RecordVersionModel)
                    .where(RecordVersionModel.superseded.is_(False))
                    .order_by(RecordVersionModel.record_type, RecordVersionModel.canonical_key)
                )
            )
            records = []
            for version in versions:
                records.append(
                    {
                        "id": str(version.id),
                        "record_type": version.record_type,
                        "canonical_key": version.canonical_key,
                        "version_number": version.version_number,
                        "payload": version.payload,
                        "evidence": await evidence_for_version(session, version),
                    }
                )
            pages = list(
                await session.scalars(
                    select(SourcePageModel).order_by(SourcePageModel.canonical_url)
                )
            )
            snapshots = list(
                await session.scalars(
                    select(SourceSnapshotModel).order_by(SourceSnapshotModel.retrieved_at)
                )
            )
            conflicts = list(await session.scalars(select(ConflictRecordModel)))
            review_tasks = list(await session.scalars(select(ReviewTaskModel)))
            return {
                "schema_version": "1.0",
                "exported_at": datetime.now(UTC).isoformat(),
                "institution_id": "uw-seattle",
                "records": records,
                "sources": [serialize_model(page) for page in pages],
                "snapshots": [
                    {
                        "id": str(snapshot.id),
                        "source_page_id": str(snapshot.source_page_id),
                        "retrieved_at": snapshot.retrieved_at.isoformat(),
                        "content_location": snapshot.raw_content_location,
                        "content_hash": snapshot.raw_content_hash,
                        "normalized_content_hash": snapshot.normalized_content_hash,
                        "content_type": snapshot.response_headers.get("content-type"),
                        "parser_version": snapshot.parser_version,
                    }
                    for snapshot in snapshots
                ],
                "conflicts": [serialize_model(conflict) for conflict in conflicts],
                "review_tasks": [serialize_model(task) for task in review_tasks],
            }
    finally:
        await engine.dispose()


def export_records(database_url: str) -> dict[str, Any]:
    return run_sync(_export_records(database_url))


def write_export(payload: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export normalized UW records with evidence")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--database-url", default=None)
    args = parser.parse_args()
    settings = Settings(database_url=args.database_url) if args.database_url else Settings()
    payload = export_records(settings.database_url)
    write_export(payload, args.output)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "records": len(payload["records"]),
                "schema_version": payload["schema_version"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
