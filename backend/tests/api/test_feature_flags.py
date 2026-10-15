from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app
from tests.factories import API


def test_ai_meal_parsing_is_disabled_by_default(client):
    assert get_settings().feature_ai_meal_parsing is False
    assert client.post(f"{API}/ai/meal-parse").status_code == 404


def test_ai_meal_parsing_flag_mounts_placeholder(monkeypatch):
    monkeypatch.setattr(get_settings(), "feature_ai_meal_parsing", True)
    client = TestClient(create_app(), base_url="https://testserver")
    assert client.post(f"{API}/ai/meal-parse").status_code == 501
