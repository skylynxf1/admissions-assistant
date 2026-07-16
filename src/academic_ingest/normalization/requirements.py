from academic_ingest.normalization.identifiers import normalize_course_code


def normalize_allowed_courses(values: list[str]) -> list[str]:
    canonical = [normalize_course_code(value)[2] for value in values]
    return list(dict.fromkeys(canonical))
