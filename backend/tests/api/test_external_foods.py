from decimal import Decimal

import pytest

from app.config import get_settings
from app.nutrition import food_sources
from app.nutrition.food_sources import ExternalFood, FoodSourceError
from tests.factories import API, onboard


class CountingSource:
    name = "mock"

    def __init__(self, fail: bool = False) -> None:
        self.calls = 0
        self.fail = fail

    def search(self, query: str, limit: int) -> list[ExternalFood]:
        self.calls += 1
        if self.fail:
            raise FoodSourceError
        return [
            ExternalFood(
                "mock",
                f"{query}-1",
                f"{query} produs",
                Decimal(100),
                Decimal(5),
                Decimal(10),
                Decimal(2),
            ),
        ]


@pytest.fixture
def source(monkeypatch):
    fake = CountingSource()
    monkeypatch.setattr(get_settings(), "food_source", "mock")
    monkeypatch.setattr("app.nutrition.service.get_food_source", lambda name: fake)
    return fake


def test_local_search_never_calls_the_external_source(make_user, source):
    c = make_user()
    onboard(c)
    c.get(f"{API}/foods", params={"q": "hummus"})
    assert source.calls == 0


def test_external_search_caches_results_and_terms(make_user, source):
    c = make_user()
    onboard(c)
    found = c.get(f"{API}/foods/external", params={"q": "hummus"}).json()
    assert found[0]["source"] == "external" and found[0]["attribution"] == "Mock"
    # Same term again: served from the database, no second external call.
    again = c.get(f"{API}/foods/external", params={"q": "hummus"}).json()
    assert again[0]["id"] == found[0]["id"] and source.calls == 1
    # Cached foods are then found by the normal local search too.
    local = c.get(f"{API}/foods", params={"q": "hummus"}).json()
    assert found[0]["id"] in [f["id"] for f in local]


def test_external_search_is_rate_limited_per_user(make_user, source):
    c = make_user()
    onboard(c)
    codes = [c.get(f"{API}/foods/external", params={"q": f"term{i}"}).status_code for i in range(5)]
    assert codes == [200, 200, 200, 200, 429]


def test_external_source_down_returns_503(make_user, monkeypatch):
    monkeypatch.setattr(get_settings(), "food_source", "mock")
    monkeypatch.setattr(
        "app.nutrition.service.get_food_source", lambda name: CountingSource(fail=True)
    )
    c = make_user()
    onboard(c)
    r = c.get(f"{API}/foods/external", params={"q": "hummus"})
    assert r.status_code == 503 and r.json()["detail"] == "food_source_unavailable"


def test_external_search_disabled_by_default(make_user):
    c = make_user()
    onboard(c)
    assert c.get(f"{API}/foods/external", params={"q": "hummus"}).status_code == 404


def test_default_adapter_is_wired(monkeypatch):
    monkeypatch.setattr(get_settings(), "off_user_agent", "Test/1.0 (test@example.com)")
    source = food_sources.get_food_source("open_food_facts")
    assert isinstance(source, food_sources.OpenFoodFactsSource)
    assert source.user_agent == "Test/1.0 (test@example.com)"
