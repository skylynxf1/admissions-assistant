from academic_ingest.snapshots.hashing import normalized_hash, raw_hash
from academic_ingest.snapshots.storage import SnapshotStore


def test_normalized_hash_ignores_insignificant_whitespace() -> None:
    assert normalized_hash(b"A  policy\nrow") == normalized_hash(b"A policy row")
    assert raw_hash(b"A  policy\nrow") != raw_hash(b"A policy row")


def test_snapshot_store_is_content_addressed_and_idempotent(tmp_path) -> None:
    store = SnapshotStore(tmp_path)

    first = store.put(b"immutable body", suffix="html")
    second = store.put(b"immutable body", suffix=".html")

    assert first == second
    assert first.path.read_bytes() == b"immutable body"
    assert first.path.name == f"{first.raw_content_hash}.html"
    assert first.location.startswith("file:")
