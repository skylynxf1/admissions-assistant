from __future__ import annotations

from pathlib import Path

from academic_ingest.config.settings import load_institution_config
from academic_ingest.validation.source_scope import uw_seattle_scope, validate_source_scope


def test_generic_pass_within_allowed_scope() -> None:
    issues = validate_source_scope(
        "https://www.washington.edu/students/crscat/",
        "Seattle",
        allowed_hosts={"washington.edu"},
        destination_campus="Seattle",
        disallowed_campus_patterns=set(),
    )

    assert issues == []


def test_generic_rejects_url_outside_allowed_hosts() -> None:
    issues = validate_source_scope(
        "http://evil.example/students/crscat/",
        "Seattle",
        allowed_hosts={"washington.edu"},
        destination_campus="Seattle",
        disallowed_campus_patterns=set(),
    )

    codes = [issue.code for issue in issues]
    assert "source_outside_official_scope" in codes


def test_generic_rejects_disallowed_campus_pattern() -> None:
    issues = validate_source_scope(
        "https://www.washington.edu/bothell/catalog",
        "Bothell",
        allowed_hosts={"washington.edu"},
        destination_campus="Seattle",
        disallowed_campus_patterns={"bothell", "tacoma"},
    )

    codes = [issue.code for issue in issues]
    assert "campus_out_of_scope" in codes


def test_uw_seattle_scope_wrapper_preserves_current_behavior() -> None:
    assert uw_seattle_scope("https://admit.washington.edu/x", "Seattle") == []

    issues = uw_seattle_scope("https://admit.washington.edu/x", "Bothell")
    codes = [issue.code for issue in issues]
    assert "campus_out_of_scope" in codes


def test_uw_seattle_scope_accepts_washington_edu_subdomain() -> None:
    """Subdomain of washington.edu should be accepted."""
    issues = uw_seattle_scope("https://admit.washington.edu/apply", "Seattle")
    assert issues == []


def test_uw_seattle_scope_accepts_uw_edu_subdomain() -> None:
    """Subdomain of uw.edu should be accepted (intended behavior)."""
    issues = uw_seattle_scope("https://my.uw.edu/x", "Seattle")
    assert issues == []


def test_uw_seattle_scope_rejects_non_official_host() -> None:
    """Non-official host should be rejected with source_outside_official_scope."""
    issues = uw_seattle_scope("https://notuw.example.com/x", "Seattle")
    codes = [issue.code for issue in issues]
    assert "source_outside_official_scope" in codes


def test_uw_seattle_scope_rejects_tacoma_campus() -> None:
    """Tacoma campus should be rejected even on official host."""
    issues = uw_seattle_scope("https://admit.washington.edu/x", "Tacoma")
    codes = [issue.code for issue in issues]
    assert "campus_out_of_scope" in codes


def test_bellevue_college_config_loads() -> None:
    config = load_institution_config(Path("config/institutions/bellevue_college.yaml"))
    assert config.institution_id == "bellevue-college"


def test_seattle_university_config_loads() -> None:
    config = load_institution_config(Path("config/institutions/seattle_university.yaml"))
    assert config.institution_id == "seattle-university"
