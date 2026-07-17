from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from academic_ingest.db.models import (
    RecordVersionModel,
    SourceChangeEventModel,
    SourcePageModel,
    SourceSnapshotModel,
    utc_now,
)
from academic_ingest.models.domain import SourcePage


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _normalized_hash(content: bytes) -> str:
    return _sha256(b" ".join(content.split()))


@dataclass(frozen=True)
class ChangedBlock:
    previous_start: int
    previous_end: int
    current_start: int
    current_end: int
    previous: list[str]
    current: list[str]


def compute_changed_blocks(previous: bytes, current: bytes) -> list[ChangedBlock]:
    previous_lines = previous.decode("utf-8", errors="replace").splitlines()
    current_lines = current.decode("utf-8", errors="replace").splitlines()
    matcher = SequenceMatcher(a=previous_lines, b=current_lines, autojunk=False)
    return [
        ChangedBlock(i1, i2, j1, j2, previous_lines[i1:i2], current_lines[j1:j2])
        for tag, i1, i2, j1, j2 in matcher.get_opcodes()
        if tag != "equal"
    ]


class SourceRepository:
    def __init__(
        self,
        session: AsyncSession,
        *,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.session = session
        self.clock = clock

    async def upsert_page(self, page: SourcePage) -> SourcePageModel:
        existing = await self.session.scalar(
            select(SourcePageModel).where(
                SourcePageModel.institution_id == page.institution_id,
                SourcePageModel.canonical_url == page.canonical_url,
            )
        )
        if existing is None:
            existing = SourcePageModel(
                id=page.id,
                institution_id=page.institution_id,
                canonical_url=page.canonical_url,
                final_url=page.final_url,
                page_title=page.page_title,
                source_type=page.source_type.value,
                policy_family=page.policy_family.value,
                campus=page.campus,
                http_status=page.http_status,
                content_type=page.content_type,
                language=page.language,
                first_seen_at=page.first_seen_at,
                last_seen_at=page.last_seen_at,
            )
            self.session.add(existing)
        else:
            existing.final_url = page.final_url
            existing.page_title = page.page_title
            existing.http_status = page.http_status
            existing.content_type = page.content_type
            existing.last_seen_at = page.last_seen_at
        await self.session.commit()
        return existing

    async def create_snapshot(
        self,
        source_page_id: UUID,
        raw_content: bytes,
        crawl_job_id: UUID | str,
        *,
        response_headers: dict[str, str] | None = None,
        parser_version: str = "snapshot-v1",
        raw_content_location: str | None = None,
        previous_raw_content: bytes | None = None,
    ) -> SourceSnapshotModel:
        raw_hash = _sha256(raw_content)
        existing = await self.session.scalar(
            select(SourceSnapshotModel).where(
                SourceSnapshotModel.source_page_id == source_page_id,
                SourceSnapshotModel.raw_content_hash == raw_hash,
            )
        )
        if existing is not None:
            return existing

        previous = await self.session.scalar(
            select(SourceSnapshotModel)
            .where(SourceSnapshotModel.source_page_id == source_page_id)
            .order_by(SourceSnapshotModel.retrieved_at.desc(), SourceSnapshotModel.id.desc())
            .limit(1)
        )
        retrieved_at = self.clock()
        if previous is not None and retrieved_at <= previous.retrieved_at:
            retrieved_at = previous.retrieved_at + timedelta(microseconds=1)
        crawl_uuid = UUID(crawl_job_id) if isinstance(crawl_job_id, str) else crawl_job_id
        snapshot = SourceSnapshotModel(
            source_page_id=source_page_id,
            crawl_job_id=crawl_uuid,
            retrieved_at=retrieved_at,
            raw_content_location=raw_content_location or f"memory://sha256/{raw_hash}",
            raw_content_hash=raw_hash,
            normalized_content_hash=_normalized_hash(raw_content),
            response_headers=response_headers or {},
            parser_version=parser_version,
        )
        self.session.add(snapshot)
        await self.session.flush()
        if previous is not None and previous_raw_content is not None:
            changes = compute_changed_blocks(previous_raw_content, raw_content)
            self.session.add(
                SourceChangeEventModel(
                    source_page_id=source_page_id,
                    previous_snapshot_id=previous.id,
                    current_snapshot_id=snapshot.id,
                    changed_blocks=[asdict(change) for change in changes],
                    material=False,
                )
            )
        await self.session.commit()
        return snapshot

    async def list_snapshots(self, source_page_id: UUID) -> list[SourceSnapshotModel]:
        result = await self.session.scalars(
            select(SourceSnapshotModel)
            .where(SourceSnapshotModel.source_page_id == source_page_id)
            .order_by(SourceSnapshotModel.retrieved_at, SourceSnapshotModel.id)
        )
        return list(result)


class VersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def publish(
        self,
        *,
        record_type: str,
        canonical_key: str,
        payload: dict[str, Any],
        evidence_record_ids: list[UUID] | None = None,
        commit: bool = True,
    ) -> RecordVersionModel:
        canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        content_hash = _sha256(canonical_payload.encode())
        existing = await self.session.scalar(
            select(RecordVersionModel).where(
                RecordVersionModel.record_type == record_type,
                RecordVersionModel.canonical_key == canonical_key,
                RecordVersionModel.content_hash == content_hash,
            )
        )
        if existing is not None:
            return existing

        current = await self.current(record_type, canonical_key)
        version_number = 1
        if current is not None:
            current.superseded = True
            version_number = current.version_number + 1
        version = RecordVersionModel(
            record_type=record_type,
            canonical_key=canonical_key,
            version_number=version_number,
            payload=payload,
            content_hash=content_hash,
            evidence_record_ids=[str(item) for item in evidence_record_ids or []],
            superseded=False,
        )
        self.session.add(version)
        if commit:
            await self.session.commit()
        else:
            await self.session.flush()
        return version

    async def current(self, record_type: str, canonical_key: str) -> RecordVersionModel | None:
        result = await self.session.execute(
            select(RecordVersionModel).where(
                RecordVersionModel.record_type == record_type,
                RecordVersionModel.canonical_key == canonical_key,
                RecordVersionModel.superseded.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def list_versions(self, record_type: str, canonical_key: str) -> list[RecordVersionModel]:
        result = await self.session.scalars(
            select(RecordVersionModel)
            .where(
                RecordVersionModel.record_type == record_type,
                RecordVersionModel.canonical_key == canonical_key,
            )
            .order_by(RecordVersionModel.version_number)
        )
        return list(result)
