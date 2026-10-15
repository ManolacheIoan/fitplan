from tests.factories import API, onboard


def first_plan_exercise(client):
    plan = client.get(f"{API}/plans/current").json()
    day = plan["days"][0]
    return day, day["exercises"][0]


def test_alternatives_same_pattern_and_level_not_already_in_day(make_user):
    c = make_user()
    onboard(c, experience="beginner")
    day, item = first_plan_exercise(c)
    alternatives = c.get(f"{API}/plans/exercises/{item['id']}/alternatives").json()
    assert alternatives
    in_day = {e["exercise"]["id"] for e in day["exercises"]}
    for alt in alternatives:
        assert alt["pattern"] == item["exercise"]["pattern"]
        assert alt["difficulty"] == "beginner"
        assert alt["id"] not in in_day


def test_permanent_swap_updates_plan_and_prescription(make_user):
    c = make_user()
    onboard(c, experience="advanced", goal="gain")
    _, item = first_plan_exercise(c)
    alternatives = c.get(f"{API}/plans/exercises/{item['id']}/alternatives").json()
    target = alternatives[0]
    r = c.patch(f"{API}/plans/exercises/{item['id']}", json={"exercise_id": target["id"]})
    assert r.status_code == 200
    assert r.json()["exercise"]["id"] == target["id"]
    _, updated = first_plan_exercise(c)
    assert updated["exercise"]["id"] == target["id"]
    assert updated["id"] == item["id"]


def test_permanent_swap_rejects_other_patterns(make_user):
    c = make_user()
    onboard(c)
    day, item = first_plan_exercise(c)
    other = day["exercises"][1]["exercise"]["id"]  # different pattern, already in the day
    r = c.patch(f"{API}/plans/exercises/{item['id']}", json={"exercise_id": other})
    assert r.status_code == 422 and r.json()["detail"] == "exercise_not_allowed"


def test_swap_for_today_only(make_user):
    c = make_user()
    onboard(c)
    today = c.get(f"{API}/workouts/today").json()
    w = c.post(f"{API}/workouts", json={"plan_day_id": today["next_day"]["id"]}).json()
    planned = w["exercises"][0]["planned"]
    alt = c.get(f"{API}/plans/exercises/{planned['id']}/alternatives").json()[0]

    r = c.post(
        f"{API}/workouts/{w['id']}/swaps",
        json={"plan_exercise_id": planned["id"], "exercise_id": alt["id"]},
    )
    assert r.status_code == 200
    swapped = r.json()["exercises"][0]
    assert swapped["swapped_today"] is True
    assert swapped["planned"]["exercise"]["id"] == alt["id"]
    # The plan itself is unchanged.
    _, in_plan = first_plan_exercise(c)
    assert in_plan["exercise"]["id"] == planned["exercise"]["id"]

    # Sets can be logged for the replacement, and then the swap is locked.
    r = c.post(
        f"{API}/workouts/{w['id']}/sets",
        json={"exercise_id": alt["id"], "weight_kg": 10, "reps": 10},
    )
    assert r.status_code == 201
    r = c.post(
        f"{API}/workouts/{w['id']}/swaps",
        json={"plan_exercise_id": planned["id"], "exercise_id": planned["exercise"]["id"]},
    )
    assert r.status_code == 409 and r.json()["detail"] == "sets_already_logged"
    assert c.get(f"{API}/account/export").json()["workouts"][0]["swaps"]


def test_swap_back_to_planned_exercise_undoes_it(make_user):
    c = make_user()
    onboard(c)
    today = c.get(f"{API}/workouts/today").json()
    w = c.post(f"{API}/workouts", json={"plan_day_id": today["next_day"]["id"]}).json()
    planned = w["exercises"][0]["planned"]
    alt = c.get(f"{API}/plans/exercises/{planned['id']}/alternatives").json()[0]
    url = f"{API}/workouts/{w['id']}/swaps"
    c.post(url, json={"plan_exercise_id": planned["id"], "exercise_id": alt["id"]})
    back = c.post(
        url, json={"plan_exercise_id": planned["id"], "exercise_id": planned["exercise"]["id"]}
    ).json()
    assert back["exercises"][0]["swapped_today"] is False
    assert back["exercises"][0]["planned"]["exercise"]["id"] == planned["exercise"]["id"]


def test_permanent_swap_refused_when_sets_logged_in_open_session(make_user):
    c = make_user()
    onboard(c)
    today = c.get(f"{API}/workouts/today").json()
    w = c.post(f"{API}/workouts", json={"plan_day_id": today["next_day"]["id"]}).json()
    planned = w["exercises"][0]["planned"]
    c.post(
        f"{API}/workouts/{w['id']}/sets",
        json={"exercise_id": planned["exercise"]["id"], "weight_kg": 10, "reps": 10},
    )
    alt = c.get(f"{API}/plans/exercises/{planned['id']}/alternatives").json()[0]
    r = c.patch(f"{API}/plans/exercises/{planned['id']}", json={"exercise_id": alt["id"]})
    assert r.status_code == 409


def test_swaps_are_private(make_user):
    owner, intruder = make_user(), make_user()
    onboard(owner)
    onboard(intruder)
    today = owner.get(f"{API}/workouts/today").json()
    w = owner.post(f"{API}/workouts", json={"plan_day_id": today["next_day"]["id"]}).json()
    planned = w["exercises"][0]["planned"]
    alt = owner.get(f"{API}/plans/exercises/{planned['id']}/alternatives").json()[0]

    assert intruder.get(f"{API}/plans/exercises/{planned['id']}/alternatives").status_code == 404
    r = intruder.patch(f"{API}/plans/exercises/{planned['id']}", json={"exercise_id": alt["id"]})
    assert r.status_code == 404
    r = intruder.post(
        f"{API}/workouts/{w['id']}/swaps",
        json={"plan_exercise_id": planned["id"], "exercise_id": alt["id"]},
    )
    assert r.status_code == 404
