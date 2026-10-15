from datetime import date, timedelta

from app.config import get_settings
from tests.factories import API, onboard

TODAY = date.today().isoformat()


def test_search_seeded_foods_ignores_diacritics(make_user):
    c = make_user()
    onboard(c)
    names = [f["name"] for f in c.get(f"{API}/foods", params={"q": "mar"}).json()]
    assert "Măr" in names
    assert c.get(f"{API}/foods", params={"q": "a"}).status_code == 422


def test_manual_food_is_private(make_user):
    owner, other = make_user(), make_user()
    onboard(owner)
    onboard(other)
    food = {
        "name": "Plăcintă bunica",
        "kcal_100g": 280,
        "protein_100g": 6,
        "carbs_100g": 35,
        "fat_100g": 12,
    }
    r = owner.post(f"{API}/foods", json=food)
    assert r.status_code == 201 and r.json()["is_own"] is True and r.json()["source"] == "manual"
    food_id = r.json()["id"]

    assert [f["id"] for f in owner.get(f"{API}/foods", params={"q": "placinta"}).json()] == [
        food_id
    ]
    assert other.get(f"{API}/foods", params={"q": "placinta"}).json() == []
    r = other.post(f"{API}/meals", json={"food_id": food_id, "eaten_on": TODAY, "grams": 100})
    assert r.status_code == 404


def test_manual_food_validation(make_user):
    c = make_user()
    onboard(c)
    base = {"name": "X food", "kcal_100g": 100, "protein_100g": 10, "carbs_100g": 10, "fat_100g": 5}
    assert c.post(f"{API}/foods", json={**base, "kcal_100g": -1}).status_code == 422
    assert c.post(f"{API}/foods", json={**base, "carbs_100g": 95}).status_code == 422


def test_daily_totals_versus_targets(make_user):
    c = make_user()
    onboard(c)
    oats = c.get(f"{API}/foods", params={"q": "ovaz"}).json()[0]
    meal = c.post(
        f"{API}/meals", json={"food_id": oats["id"], "eaten_on": TODAY, "grams": 50}
    ).json()
    assert meal["kcal"] == "189.5"  # 379 kcal/100 g * 50 g

    day = c.get(f"{API}/meals", params={"date": TODAY}).json()
    assert day["totals"]["kcal"] == "189.5"
    assert day["targets"]["kcal"] > 0

    c.patch(f"{API}/meals/{meal['id']}", json={"grams": 100})
    assert c.get(f"{API}/meals", params={"date": TODAY}).json()["totals"]["kcal"] == "379.0"
    assert c.delete(f"{API}/meals/{meal['id']}").status_code == 204
    assert c.get(f"{API}/meals", params={"date": TODAY}).json()["entries"] == []


def test_meal_date_and_grams_validation(make_user):
    c = make_user()
    onboard(c)
    food_id = c.get(f"{API}/foods", params={"q": "banana"}).json()[0]["id"]
    future = (date.today() + timedelta(days=5)).isoformat()
    for bad in (
        {"eaten_on": future, "grams": 100},
        {"eaten_on": TODAY, "grams": 0},
        {"eaten_on": TODAY, "grams": 99999},
    ):
        assert c.post(f"{API}/meals", json={"food_id": food_id, **bad}).status_code == 422


def test_users_cannot_touch_each_others_meals(make_user):
    owner, intruder = make_user(), make_user()
    onboard(owner)
    onboard(intruder)
    food_id = owner.get(f"{API}/foods", params={"q": "banana"}).json()[0]["id"]
    meal_id = owner.post(
        f"{API}/meals", json={"food_id": food_id, "eaten_on": TODAY, "grams": 120}
    ).json()["id"]
    assert intruder.patch(f"{API}/meals/{meal_id}", json={"grams": 1}).status_code == 404
    assert intruder.delete(f"{API}/meals/{meal_id}").status_code == 404
    assert intruder.get(f"{API}/meals", params={"date": TODAY}).json()["entries"] == []


def test_external_source_results_are_cached(make_user, monkeypatch):
    monkeypatch.setattr(get_settings(), "food_source", "mock")
    c = make_user()
    onboard(c)
    found = c.get(f"{API}/foods", params={"q": "hummus"}).json()
    assert found and found[0]["source"] == "external"
    monkeypatch.setattr(get_settings(), "food_source", "none")
    # Served from the local cache once the source is disabled.
    assert c.get(f"{API}/foods", params={"q": "hummus"}).json()[0]["id"] == found[0]["id"]
