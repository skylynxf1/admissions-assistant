from academic_ingest.discovery.robots import RobotsPolicy


def test_robots_policy_honors_specific_user_agent_rules() -> None:
    policy = RobotsPolicy.from_text(
        "https://www.washington.edu/robots.txt",
        """
        User-agent: AcademicPlanningOS
        Disallow: /private/
        Allow: /private/public.html
        """,
        user_agent="AcademicPlanningOS",
    )

    assert policy.evaluate("https://www.washington.edu/catalog").allowed is True
    assert policy.evaluate("https://www.washington.edu/private/data").allowed is False
    assert policy.evaluate("https://www.washington.edu/private/public.html").allowed is True


def test_robots_policy_rejects_cross_origin_checks() -> None:
    policy = RobotsPolicy.from_text(
        "https://www.washington.edu/robots.txt",
        "User-agent: *\nDisallow:",
        user_agent="AcademicPlanningOS",
    )

    decision = policy.evaluate("https://admit.washington.edu/apply")

    assert decision.allowed is False
    assert "origin" in decision.reason.lower()
