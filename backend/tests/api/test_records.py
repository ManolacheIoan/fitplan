from tests.factories import API, onboard


def start(client):
    today = client.get(f"{API}/workouts/today").json()
    return client.post(f"{API}/workouts", json={"plan_day_id": today["next_day"]["id"]}).json()


def log(client, workout, exercise_id, kg, reps):
    r = client.post(
        f"{API}/workouts/{workout['id']}/sets",
        json={"exercise_id": exercise_id, "weight_kg": kg, "reps": reps},
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_records_are_the_heaviest_weight_per_exercise(make_user):
    c = make_user()
    onboard(c)
    w = start(c)
    exercise = w["exercises"][0]["planned"]["exercise"]
    assert log(c, w, exercise["id"], 40, 10)["is_record"] is False  # first ever: no record yet
    assert log(c, w, exercise["id"], 50, 5)["is_record"] is True
    assert log(c, w, exercise["id"], 50, 8)["is_record"] is False  # equal weight is not a record
    assert log(c, w, exercise["id"], 45, 12)["is_record"] is False

    records = c.get(f"{API}/progress/records").json()
    assert len(records) == 1
    record = records[0]
    assert record["exercise_name"] == exercise["name"]
    # Ties on weight are broken by more reps.
    assert (record["weight_kg"], record["reps"]) == ("50.00", 8)


def test_sets_without_external_load_are_not_records(make_user):
    c = make_user()
    onboard(c)
    w = start(c)
    exercise_id = w["exercises"][0]["planned"]["exercise"]["id"]
    log(c, w, exercise_id, 0, 15)
    assert c.get(f"{API}/progress/records").json() == []


def test_records_are_private(make_user):
    owner, other = make_user(), make_user()
    onboard(owner)
    onboard(other)
    w = start(owner)
    log(owner, w, w["exercises"][0]["planned"]["exercise"]["id"], 60, 5)
    assert other.get(f"{API}/progress/records").json() == []
