from datetime import UTC, date, datetime, timedelta

from sqlalchemy import update

from app.nutrition.models import NutritionTarget
from tests.factories import API, onboard, profile_payload


def day(offset: int) -> str:
    return (date.today() - timedelta(days=offset)).isoformat()


def age_targets(db, days: int) -> None:
    db.execute(update(NutritionTarget).values(computed_at=datetime.now(UTC) - timedelta(days=days)))


def test_weight_entry_updates_profile_but_not_targets_within_a_week(make_user):
    c = make_user()
    onboard(c, weight_kg=70)
    before = c.get(f"{API}/nutrition/targets").json()["targets"]
    r = c.post(f"{API}/weights", json={"logged_on": day(0), "weight_kg": 69.0})
    assert r.status_code == 200 and r.json()["targets_updated"] is False
    assert c.get(f"{API}/profile").json()["weight_kg"] == "69.0"
    assert c.get(f"{API}/nutrition/targets").json()["targets"] == before


def test_targets_recomputed_from_weekly_average_after_a_week(make_user, db):
    c = make_user()
    onboard(c, weight_kg=70)
    for offset, kg in ((2, 69.0), (1, 68.0)):
        c.post(f"{API}/weights", json={"logged_on": day(offset), "weight_kg": kg})
    age_targets(db, 8)
    r = c.post(f"{API}/weights", json={"logged_on": day(0), "weight_kg": 67.0})
    assert r.json()["targets_updated"] is True
    targets = c.get(f"{API}/nutrition/targets").json()["targets"]
    assert targets["based_on_weight_kg"] == "68.0"  # (69 + 68 + 67) / 3


def test_recompute_blocks_weight_loss_when_bmi_drops_below_threshold(make_user, db):
    c = make_user()
    onboard(c, height_cm=180, weight_kg=61, goal="lose")  # BMI ~18.8
    age_targets(db, 8)
    c.post(f"{API}/weights", json={"logged_on": day(0), "weight_kg": 58.0})  # BMI ~17.9
    body = c.get(f"{API}/nutrition/targets").json()
    assert body == {"status": "blocked", "reason": "weight_loss_blocked_bmi", "targets": None}


def test_same_day_entry_is_replaced_and_backdated_entry_keeps_latest_weight(make_user):
    c = make_user()
    onboard(c)
    c.post(f"{API}/weights", json={"logged_on": day(0), "weight_kg": 70.0})
    c.post(f"{API}/weights", json={"logged_on": day(0), "weight_kg": 69.5})
    c.post(f"{API}/weights", json={"logged_on": day(3), "weight_kg": 72.0})
    entries = c.get(f"{API}/progress/weight").json()["entries"]
    assert [e["weight_kg"] for e in entries] == ["72.0", "69.5"]
    assert c.get(f"{API}/profile").json()["weight_kg"] == "69.5"


def test_weekly_average_progress(make_user):
    c = make_user()
    onboard(c)
    for offset, kg in ((14, 72.0), (13, 71.0), (0, 70.0)):
        c.post(f"{API}/weights", json={"logged_on": day(offset), "weight_kg": kg})
    weekly = c.get(f"{API}/progress/weight", params={"weeks": 4}).json()["weekly"]
    assert len(weekly) >= 2
    assert all(date.fromisoformat(w["week_start"]).weekday() == 0 for w in weekly)


def test_weight_validation_and_isolation(make_user):
    owner, intruder = make_user(), make_user()
    onboard(owner)
    onboard(intruder)
    assert (
        owner.post(f"{API}/weights", json={"logged_on": day(0), "weight_kg": 20}).status_code == 422
    )
    entry = owner.post(f"{API}/weights", json={"logged_on": day(0), "weight_kg": 70}).json()[
        "entry"
    ]
    assert intruder.delete(f"{API}/weights/{entry['id']}").status_code == 404
    assert intruder.get(f"{API}/progress/weight").json()["entries"] == []
    assert owner.delete(f"{API}/weights/{entry['id']}").status_code == 204


def test_volume_progress_counts_finished_sessions(make_user):
    c = make_user()
    onboard(c)
    today = c.get(f"{API}/workouts/today").json()
    w = c.post(f"{API}/workouts", json={"plan_day_id": today["next_day"]["id"]}).json()
    exercise_id = w["exercises"][0]["planned"]["exercise"]["id"]
    c.post(
        f"{API}/workouts/{w['id']}/sets",
        json={"exercise_id": exercise_id, "weight_kg": 50, "reps": 10},
    )
    assert c.get(f"{API}/progress/volume").json()["weekly"] == []  # not finished yet
    c.post(f"{API}/workouts/{w['id']}/finish")
    weekly = c.get(f"{API}/progress/volume").json()["weekly"]
    assert weekly[-1]["volume_kg"] == "500.00" and weekly[-1]["sessions"] == 1


def test_export_contains_all_user_data(make_user):
    c = make_user()
    onboard(c)
    c.post(f"{API}/weights", json={"logged_on": day(0), "weight_kg": 70})
    data = c.get(f"{API}/account/export").json()
    assert {
        "email",
        "consents",
        "profile",
        "nutrition_targets",
        "plans",
        "own_foods",
        "workouts",
        "meals",
        "weights",
    } <= data.keys()
    assert data["weights"][0]["weight_kg"] == "70.0"


def test_dropping_below_bmi_threshold_between_recomputes_blocks_immediately(make_user):
    c = make_user()
    onboard(c, height_cm=180, weight_kg=61, goal="lose")  # BMI ~18.8, targets just computed
    assert c.get(f"{API}/nutrition/targets").json()["status"] == "ok"
    r = c.post(f"{API}/weights", json={"logged_on": day(0), "weight_kg": 58.0})  # BMI ~17.9
    assert r.json()["targets_updated"] is True
    body = c.get(f"{API}/nutrition/targets").json()
    assert body == {"status": "blocked", "reason": "weight_loss_blocked_bmi", "targets": None}


def test_weekly_average_above_threshold_does_not_hide_current_weight(make_user, db):
    c = make_user()
    onboard(c, height_cm=180, weight_kg=62, goal="lose")
    for offset in (3, 2, 1):
        c.post(f"{API}/weights", json={"logged_on": day(offset), "weight_kg": 62.0})
    age_targets(db, 8)
    c.post(f"{API}/weights", json={"logged_on": day(0), "weight_kg": 58.0})  # average 61.0
    assert c.get(f"{API}/nutrition/targets").json()["status"] == "blocked"


def test_deleting_a_weight_entry_reapplies_the_bmi_rule(make_user):
    c = make_user()
    onboard(c, height_cm=180, weight_kg=61, goal="lose")
    c.post(f"{API}/weights", json={"logged_on": day(1), "weight_kg": 58.0})
    assert c.get(f"{API}/nutrition/targets").json()["status"] == "blocked"
    # Deleting the low entry leaves an older weight above the threshold: unblocked again.
    c.post(f"{API}/weights", json={"logged_on": day(2), "weight_kg": 61.0})
    low = next(
        e for e in c.get(f"{API}/progress/weight").json()["entries"] if e["weight_kg"] == "58.0"
    )
    assert c.delete(f"{API}/weights/{low['id']}").status_code == 204
    assert c.get(f"{API}/profile").json()["weight_kg"] == "61.0"
    assert c.get(f"{API}/nutrition/targets").json()["status"] == "ok"


def test_deleting_the_latest_entry_blocks_when_older_weight_is_below_threshold(make_user):
    c = make_user()
    onboard(c, height_cm=180, weight_kg=61, goal="lose")
    # Older than the 7-day window, so it does not pull the average below the threshold.
    c.post(f"{API}/weights", json={"logged_on": day(10), "weight_kg": 58.0})
    c.post(f"{API}/weights", json={"logged_on": day(0), "weight_kg": 61.0})
    assert c.get(f"{API}/nutrition/targets").json()["status"] == "ok"
    latest = next(
        e for e in c.get(f"{API}/progress/weight").json()["entries"] if e["weight_kg"] == "61.0"
    )
    c.delete(f"{API}/weights/{latest['id']}")
    assert c.get(f"{API}/nutrition/targets").json()["status"] == "blocked"


def test_profile_change_below_threshold_is_rejected_and_maintain_has_targets(make_user):
    c = make_user()
    onboard(c, height_cm=180, weight_kg=61, goal="lose")
    r = c.put(f"{API}/profile", json=profile_payload(height_cm=180, weight_kg=58, goal="lose"))
    assert r.status_code == 422 and r.json()["detail"] == "weight_loss_blocked_bmi"
    r = c.put(f"{API}/profile", json=profile_payload(height_cm=180, weight_kg=58, goal="maintain"))
    assert r.status_code == 200
    assert c.get(f"{API}/nutrition/targets").json()["status"] == "ok"
