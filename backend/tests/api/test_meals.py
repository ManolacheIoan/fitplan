from datetime import date, timedelta

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
    r = other.post(
        f"{API}/meals",
        json={"meal_type": "lunch", "food_id": food_id, "eaten_on": TODAY, "grams": 100},
    )
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
        f"{API}/meals",
        json={"meal_type": "lunch", "food_id": oats["id"], "eaten_on": TODAY, "grams": 50},
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
        assert (
            c.post(
                f"{API}/meals", json={"meal_type": "lunch", "food_id": food_id, **bad}
            ).status_code
            == 422
        )


def test_users_cannot_touch_each_others_meals(make_user):
    owner, intruder = make_user(), make_user()
    onboard(owner)
    onboard(intruder)
    food_id = owner.get(f"{API}/foods", params={"q": "banana"}).json()[0]["id"]
    meal_id = owner.post(
        f"{API}/meals",
        json={"meal_type": "lunch", "food_id": food_id, "eaten_on": TODAY, "grams": 120},
    ).json()["id"]
    assert intruder.patch(f"{API}/meals/{meal_id}", json={"grams": 1}).status_code == 404
    assert intruder.delete(f"{API}/meals/{meal_id}").status_code == 404
    assert intruder.get(f"{API}/meals", params={"date": TODAY}).json()["entries"] == []


def test_meal_category_required_and_editable(make_user):
    c = make_user()
    onboard(c)
    food_id = c.get(f"{API}/foods", params={"q": "banana"}).json()[0]["id"]
    body = {"food_id": food_id, "eaten_on": TODAY, "grams": 100}
    assert c.post(f"{API}/meals", json=body).status_code == 422
    assert c.post(f"{API}/meals", json={**body, "meal_type": "brunch"}).status_code == 422

    meal = c.post(f"{API}/meals", json={**body, "meal_type": "breakfast"}).json()
    assert meal["meal_type"] == "breakfast"
    updated = c.patch(f"{API}/meals/{meal['id']}", json={"grams": 120, "meal_type": "snack"}).json()
    assert (updated["meal_type"], updated["grams"]) == ("snack", "120.0")
    # Changing only the quantity keeps the category.
    kept = c.patch(f"{API}/meals/{meal['id']}", json={"grams": 90}).json()
    assert kept["meal_type"] == "snack"
    entries = c.get(f"{API}/meals", params={"date": TODAY}).json()["entries"]
    assert [e["meal_type"] for e in entries] == ["snack"]


def test_recent_foods_distinct_most_recent_first(make_user):
    c = make_user()
    onboard(c)
    banana = c.get(f"{API}/foods", params={"q": "banana"}).json()[0]["id"]
    oats = c.get(f"{API}/foods", params={"q": "ovaz"}).json()[0]["id"]
    for food_id, grams in ((banana, 100), (oats, 40), (banana, 120)):
        body = {"meal_type": "snack", "food_id": food_id, "eaten_on": TODAY, "grams": grams}
        assert c.post(f"{API}/meals", json=body).status_code == 201
    recent = c.get(f"{API}/meals/recent").json()
    assert [(r["food"]["id"], r["grams"]) for r in recent] == [(banana, "120.0"), (oats, "40.0")]
    assert len(c.get(f"{API}/meals/recent", params={"limit": 1}).json()) == 1
    assert c.get(f"{API}/meals/recent", params={"limit": 99}).status_code == 422


def test_recent_foods_are_private(make_user):
    owner, other = make_user(), make_user()
    onboard(owner)
    onboard(other)
    banana = owner.get(f"{API}/foods", params={"q": "banana"}).json()[0]["id"]
    body = {"meal_type": "snack", "food_id": banana, "eaten_on": TODAY, "grams": 100}
    owner.post(f"{API}/meals", json=body)
    assert other.get(f"{API}/meals/recent").json() == []
