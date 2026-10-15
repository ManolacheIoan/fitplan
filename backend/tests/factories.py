"""Valid request payloads shared by API tests."""

from datetime import date
from typing import Any

from fastapi.testclient import TestClient

API = "/api/v1"


def profile_payload(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "display_name": "Ana",
        "sex": "female",
        "birth_date": date(1995, 5, 20).isoformat(),
        "height_cm": 168,
        "weight_kg": 70,
        "activity_level": "moderate",
        "goal": "lose",
        "training_days": 3,
        "experience": "beginner",
        "equipment": "gym",
    }
    return {**data, **overrides}


NO_RISK = {
    "pregnant_or_breastfeeding": False,
    "diagnosed_medical_condition": False,
    "eating_disorder_history": False,
    "current_injury": False,
}


def onboard(client: TestClient, **profile: Any) -> None:
    """Create a profile and pass the screening."""
    assert client.put(f"{API}/profile", json=profile_payload(**profile)).status_code == 200
    r = client.post(f"{API}/profile/screening", json=NO_RISK)
    assert r.json()["status"] == "passed"
