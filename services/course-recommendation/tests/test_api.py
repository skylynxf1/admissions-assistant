from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from app.models import ConditionType, GroupType, PrerequisiteCondition, PrerequisiteGroup
from app.repository import InMemoryRecommendationRepository
from app.sample_data import SCENARIO_ID


def client_for(dataset):
    return TestClient(create_app(InMemoryRecommendationRepository({SCENARIO_ID: dataset})))


def test_recommendation_endpoint_returns_ranked_traceable_results(dataset):
    with client_for(dataset) as client:
        response = client.post(
            f"/api/v1/scenarios/{SCENARIO_ID}/recommendations",
            json={"target_term": "autumn-2026", "max_results": 10, "include_uncertain": True},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario_id"] == SCENARIO_ID
    assert payload["recommendations"][0]["rank"] == 1
    assert payload["recommendations"][0]["score_breakdown"]
    assert payload["recommendations"][0]["source_ids"]
    assert "Sample data only" in payload["data_warnings"][0]


def test_recommendation_endpoint_uses_deterministic_cache(dataset):
    with client_for(dataset) as client:
        path = f"/api/v1/scenarios/{SCENARIO_ID}/recommendations"
        body = {"target_term": "autumn-2026", "max_results": 2, "include_uncertain": True}
        first = client.post(path, json=body).json()
        second = client.post(path, json=body).json()
    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert first["scenario_fingerprint"] == second["scenario_fingerprint"]
    assert first["recommendations"] == second["recommendations"]


def test_recommendation_endpoint_returns_404_for_unknown_scenario(dataset):
    with client_for(dataset) as client:
        response = client.post(
            "/api/v1/scenarios/missing/recommendations",
            json={"target_term": "autumn-2026"},
        )
    assert response.status_code == 404


def test_recommendation_endpoint_rejects_prerequisite_cycle(dataset):
    dataset.prerequisite_groups.append(
        PrerequisiteGroup(
            id="cycle-a",
            target_course_id="calc1",
            group_type=GroupType.ALL,
            conditions=[PrerequisiteCondition(
                id="cycle-a-condition",
                prerequisite_group_id="cycle-a",
                condition_type=ConditionType.COURSE,
                prerequisite_course_id="calc2",
            )],
        )
    )
    with client_for(dataset) as client:
        response = client.post(
            f"/api/v1/scenarios/{SCENARIO_ID}/recommendations",
            json={"target_term": "autumn-2026"},
        )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "PREREQUISITE_CYCLE"
