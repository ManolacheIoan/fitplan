from tests.factories import API, NO_RISK, onboard, profile_payload


def test_plan_generated_after_onboarding(make_user):
    c = make_user()
    onboard(c, training_days=4, experience="intermediate")
    plan = c.get(f"{API}/plans/current").json()
    assert plan["template"] == "upper_lower"
    assert len(plan["days"]) == 4
    first = plan["days"][0]["exercises"][0]
    assert first["exercise"]["name"] and first["exercise"]["description"]
    assert first["sets"] >= 2


def test_plan_regenerated_on_relevant_change_and_history_kept(make_user):
    c = make_user()
    onboard(c, training_days=3)
    first_id = c.get(f"{API}/plans/current").json()["id"]

    # Name change does not affect the plan.
    c.put(f"{API}/profile", json=profile_payload(training_days=3, display_name="Ana Maria"))
    assert c.get(f"{API}/plans/current").json()["id"] == first_id

    c.put(f"{API}/profile", json=profile_payload(training_days=5))
    current = c.get(f"{API}/plans/current").json()
    assert current["id"] != first_id and current["template"] == "push_pull_legs"

    history = c.get(f"{API}/plans").json()
    assert [p["id"] for p in history["items"]] == [current["id"], first_id]
    assert [p["is_active"] for p in history["items"]] == [True, False]
    assert c.get(f"{API}/plans/{first_id}").json()["is_active"] is False


def test_plan_history_pagination(make_user):
    c = make_user()
    onboard(c, training_days=2)
    for days in (3, 4, 5):
        c.put(f"{API}/profile", json=profile_payload(training_days=days))
    page1 = c.get(f"{API}/plans", params={"limit": 3}).json()
    assert len(page1["items"]) == 3 and page1["next_offset"] == 3
    page2 = c.get(f"{API}/plans", params={"limit": 3, "offset": 3}).json()
    assert len(page2["items"]) == 1 and page2["next_offset"] is None
    assert c.get(f"{API}/plans", params={"limit": 500}).status_code == 422


def test_no_plan_after_screening_refer(make_user):
    c = make_user()
    onboard(c)
    c.post(f"{API}/profile/screening", json={**NO_RISK, "pregnant_or_breastfeeding": True})
    assert c.get(f"{API}/plans/current").status_code == 403
    # Passing the screening again generates a fresh plan.
    c.post(f"{API}/profile/screening", json=NO_RISK)
    assert c.get(f"{API}/plans/current").status_code == 200


def test_cannot_read_another_users_plan(make_user):
    owner, other = make_user(), make_user()
    onboard(owner)
    onboard(other)
    plan_id = owner.get(f"{API}/plans/current").json()["id"]
    assert other.get(f"{API}/plans/{plan_id}").status_code == 404
    assert plan_id not in [p["id"] for p in other.get(f"{API}/plans").json()["items"]]
