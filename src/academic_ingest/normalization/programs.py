from academic_ingest.normalization.identifiers import normalize_whitespace


def normalize_program_name(value: str) -> str:
    normalized = normalize_whitespace(value)
    if not normalized:
        raise ValueError("program name cannot be empty")
    return normalized
