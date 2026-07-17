import hashlib


def raw_hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def normalized_hash(raw: bytes) -> str:
    normalized = b" ".join(raw.split())
    return raw_hash(normalized)
