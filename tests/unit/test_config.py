from pathlib import Path

import pytest

from academic_ingest.config.settings import load_institution_config

CONFIG_PATH = Path("config/institutions/uw_seattle.yaml")


def test_uw_config_enforces_seattle_scope() -> None:
    config = load_institution_config(CONFIG_PATH)

    assert config.institution_id == "uw-seattle"
    assert config.campus == "Seattle"
    assert config.calendar_system.value == "quarter"
    assert config.is_allowed_url("https://admit.washington.edu/apply/transfer/")
    assert config.url_belongs_to_disallowed_campus("https://tacoma.uw.edu/catalog")
    assert config.url_belongs_to_disallowed_campus(
        "https://www.washington.edu/students/crscat/bothell/"
    )


def test_user_agent_requires_contact_placeholder() -> None:
    config = load_institution_config(CONFIG_PATH)

    assert config.request_policy.build_user_agent("crawler@example.org") == (
        "AcademicPlanningOS/0.1 (+crawler@example.org)"
    )
    with pytest.raises(ValueError, match="contact email"):
        config.request_policy.build_user_agent("")
