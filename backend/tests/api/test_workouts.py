from tests.factories import API, onboard


def start_today(client):
    today = client.get(f"{API}/workouts/today").json()
    r = client.post(f"{API}/workouts", json={"plan_day_id": today["next_day"]["id"]})
    assert r.status_code == 201, r.text
    return r.json()


def log_all_sets(client, workout, reps_offset=0):
    for item in workout["exercises"]:
        planned = item["planned"]
        for _ in range(planned["sets"]):
            r = client.post(
                f"{API}/workouts/{workout['id']}/sets",
                json={
                    "exercise_id": planned["exercise"]["id"],
                    "weight_kg": 20,
                    "reps": planned["reps_max"] + reps_offset,
                },
            )
            assert r.status_code == 201, r.text


def test_full_workout_flow_and_rotation(make_user):
    c = make_user()
    onboard(c, training_days=3)
    today = c.get(f"{API}/workouts/today").json()
    assert today["open_session_id"] is None and today["next_day"]["position"] == 1

    workout = start_today(c)
    assert workout["exercises"][0]["suggestion"]["kind"] == "first_time"
    assert c.get(f"{API}/workouts/today").json()["open_session_id"] == workout["id"]
    # Only one open session at a time.
    r = c.post(f"{API}/workouts", json={"plan_day_id": workout["day"]["id"]})
    assert r.status_code == 409

    log_all_sets(c, workout)
    detail = c.get(f"{API}/workouts/{workout['id']}").json()
    first = detail["exercises"][0]
    assert [s["set_number"] for s in first["sets"]] == list(range(1, len(first["sets"]) + 1))

    assert c.post(f"{API}/workouts/{workout['id']}/finish").status_code == 204
    assert c.get(f"{API}/workouts/today").json()["next_day"]["position"] == 2

    history = c.get(f"{API}/workouts").json()
    assert history["items"][0]["sets_count"] == sum(
        e["planned"]["sets"] for e in workout["exercises"]
    )
    assert float(history["items"][0]["volume_kg"]) > 0


def test_progression_suggestion_uses_last_session(make_user):
    c = make_user()
    onboard(c, training_days=2)
    for _ in range(2):  # day 1 and day 2
        w = start_today(c)
        log_all_sets(c, w)
        c.post(f"{API}/workouts/{w['id']}/finish")
    third = start_today(c)  # day 1 again
    suggestion = third["exercises"][0]["suggestion"]
    assert suggestion["kind"] == "add_weight"
    assert float(suggestion["weight_kg"]) > 20
    assert third["exercises"][0]["last_sets"]


def test_edit_and_delete_sets(make_user):
    c = make_user()
    onboard(c)
    w = start_today(c)
    exercise_id = w["exercises"][0]["planned"]["exercise"]["id"]
    ids = [
        c.post(
            f"{API}/workouts/{w['id']}/sets",
            json={"exercise_id": exercise_id, "weight_kg": 40, "reps": 8},
        ).json()["id"]
        for _ in range(3)
    ]
    r = c.patch(f"{API}/sets/{ids[0]}", json={"reps": 10, "weight_kg": 42.5})
    assert r.json()["reps"] == 10 and r.json()["weight_kg"] == "42.50"
    assert c.delete(f"{API}/sets/{ids[0]}").status_code == 204
    sets = c.get(f"{API}/workouts/{w['id']}").json()["exercises"][0]["sets"]
    assert [s["set_number"] for s in sets] == [1, 2]


def test_set_validation(make_user):
    c = make_user()
    onboard(c)
    w = start_today(c)
    exercise_id = w["exercises"][0]["planned"]["exercise"]["id"]
    url = f"{API}/workouts/{w['id']}/sets"
    assert (
        c.post(url, json={"exercise_id": exercise_id, "weight_kg": -1, "reps": 5}).status_code
        == 422
    )
    assert (
        c.post(url, json={"exercise_id": exercise_id, "weight_kg": 10, "reps": 0}).status_code
        == 422
    )
    other_exercise = 999999
    r = c.post(url, json={"exercise_id": other_exercise, "weight_kg": 10, "reps": 5})
    assert r.status_code == 422 and r.json()["detail"] == "exercise_not_in_workout"


def test_users_cannot_touch_each_others_workouts(make_user):
    owner, intruder = make_user(), make_user()
    onboard(owner)
    onboard(intruder)
    w = start_today(owner)
    exercise_id = w["exercises"][0]["planned"]["exercise"]["id"]
    set_id = owner.post(
        f"{API}/workouts/{w['id']}/sets",
        json={"exercise_id": exercise_id, "weight_kg": 10, "reps": 5},
    ).json()["id"]

    assert intruder.get(f"{API}/workouts/{w['id']}").status_code == 404
    assert intruder.post(f"{API}/workouts/{w['id']}/finish").status_code == 404
    r = intruder.post(
        f"{API}/workouts/{w['id']}/sets",
        json={"exercise_id": exercise_id, "weight_kg": 10, "reps": 5},
    )
    assert r.status_code == 404
    assert intruder.patch(f"{API}/sets/{set_id}", json={"reps": 1}).status_code == 404
    assert intruder.delete(f"{API}/sets/{set_id}").status_code == 404
    # Starting a session on someone else's plan day is refused.
    assert intruder.post(f"{API}/workouts", json={"plan_day_id": w["day"]["id"]}).status_code == 404
    assert intruder.get(f"{API}/workouts").json()["items"] == []
