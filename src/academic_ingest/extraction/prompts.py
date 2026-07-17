PROMPT_VERSION = "academic-policy-extraction-2026-07-16.1"
SCHEMA_VERSION = "1.0"

BASE_INSTRUCTIONS = """You extract academic policy claims only from the supplied context.
Return strict structured output. Every proposed claim must include an exact supporting evidence
string copied from the supplied content. Preserve unknown and ambiguous fields. Do not browse,
use general knowledge, guess equivalencies, convert recommendations into requirements, introduce
new URLs, assign final confidence, or silently override known deterministic fields."""

OPERATION_INSTRUCTIONS = {
    "classify_page": "Classify the supplied page without inventing a policy family.",
    "extract_course_requirement": "Extract only source-supported course requirement fields.",
    "parse_requirement_expression": "Represent the requirement while preserving nested logic.",
    "extract_policy": "Extract only source-supported academic policy fields.",
    "compare_sources": "List field-level agreements and conflicts without choosing a winner.",
    "summarize_unresolved_issue": "Summarize the unresolved issue as a reviewer question.",
}


def instructions_for(operation: str) -> str:
    try:
        operation_instruction = OPERATION_INSTRUCTIONS[operation]
    except KeyError as error:
        raise ValueError(f"unsupported structured extraction operation: {operation}") from error
    return f"{BASE_INSTRUCTIONS}\n\nOperation: {operation_instruction}"

