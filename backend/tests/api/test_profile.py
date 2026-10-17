from datetime import date, timedelta

from sqlalchemy import delete, inspect

from app.auth.models import Consent
from app.profile.models import Profile
from tests.factories import API, NO_RISK, onboard, profile_payload


def years_ago(years: int, extra_days: int = 0) -> str:
    today = date.today()
    if (today.month, today.day) == (2, 29):  # keep the helper valid on leap days
        today -= timedelta(days=1)
    return (today.replace(year=today.year - years) + timedelta(days=extra_days)).isoformat()


def test_profile_missing_initially(make_user):
    assert make_user().get(f"{API}/profile").status_code == 404


def test_create_and_read_profile(make_user):
    c = make_user()
    r = c.put(f"{API}/profile", json=profile_payload(display_name="  Ana  "))
    assert r.status_code == 200
    body = c.get(f"{API}/profile").json()
    assert body["display_name"] == "Ana"
    assert body["age"] >= 18
    assert body["screening_status"] is None


def test_underage_is_blocked_server_side(make_user):
    c = make_user()
    r = c.put(f"{API}/profile", json=profile_payload(birth_date=years_ago(18, extra_days=1)))
    assert r.status_code == 422 and r.json()["detail"] == "underage"
    assert (
        c.put(f"{API}/profile", json=profile_payload(birth_date=years_ago(18))).status_code == 200
    )


def test_weight_loss_goal_blocked_at_low_bmi(make_user):
    c = make_user()
    low = profile_payload(height_cm=180, weight_kg=58, goal="lose")  # BMI ~17.9
    r = c.put(f"{API}/profile", json=low)
    assert r.status_code == 422 and r.json()["detail"] == "weight_loss_blocked_bmi"
    assert c.put(f"{API}/profile", json={**low, "goal": "maintain"}).status_code == 200


def test_input_ranges_are_validated(make_user):
    c = make_user()
    for bad in (
        {"height_cm": 90},
        {"weight_kg": -5},
        {"training_days": 7},
        {"sex": "other"},
        {"display_name": "   "},
        {"height_cm": 170.55},
    ):
        assert c.put(f"{API}/profile", json=profile_payload(**bad)).status_code == 422, bad


def test_screening_requires_profile(make_user):
    assert make_user().post(f"{API}/profile/screening", json=NO_RISK).status_code == 409


def test_screening_stores_only_outcome(make_user, db):
    c = make_user()
    c.put(f"{API}/profile", json=profile_payload())
    r = c.post(f"{API}/profile/screening", json={**NO_RISK, "current_injury": True})
    assert r.json() == {"status": "refer"}

    columns = {col.key for col in inspect(Profile).columns}
    assert not {"pregnant_or_breastfeeding", "current_injury"} & columns
    body = c.get(f"{API}/profile").json()
    assert body["screening_status"] == "refer" and body["screening_at"]

    # Retaking the screening is possible.
    assert c.post(f"{API}/profile/screening", json=NO_RISK).json() == {"status": "passed"}


def test_screening_answers_must_be_booleans(make_user):
    c = make_user()
    c.put(f"{API}/profile", json=profile_payload())
    bad = {**NO_RISK, "current_injury": "maybe"}
    assert c.post(f"{API}/profile/screening", json=bad).status_code == 422


def test_profile_requires_consent(make_user, db):
    c = make_user()
    db.execute(delete(Consent))
    assert c.get(f"{API}/profile").status_code == 403


def test_profile_in_export(make_user):
    c = make_user()
    onboard(c)
    assert c.get(f"{API}/account/export").json()["profile"]["display_name"] == "Ana"


def test_pregnancy_question_only_applies_to_female(make_user):
    male = make_user()
    male.put(f"{API}/profile", json=profile_payload(sex="male"))
    answers = {k: v for k, v in NO_RISK.items() if k != "pregnant_or_breastfeeding"}
    assert male.post(f"{API}/profile/screening", json=answers).json() == {"status": "passed"}
    # Even if a client sends it, the answer is ignored for male sex.
    sent = {**answers, "pregnant_or_breastfeeding": True}
    assert male.post(f"{API}/profile/screening", json=sent).json() == {"status": "passed"}

    female = make_user()
    female.put(f"{API}/profile", json=profile_payload(sex="female"))
    r = female.post(f"{API}/profile/screening", json=answers)
    assert r.status_code == 422 and r.json()["detail"] == "pregnancy_answer_required"


def test_male_to_female_after_passed_screening_requires_screening_again(make_user):
    c = make_user()
    onboard(c, sex="male")
    assert c.get(f"{API}/plans/current").status_code == 200
    r = c.put(f"{API}/profile", json=profile_payload(sex="female"))
    assert r.status_code == 200 and r.json()["screening_status"] is None
    for path in ("/nutrition/targets", "/plans/current", "/workouts/today"):
        r = c.get(f"{API}{path}")
        assert r.status_code == 409 and r.json()["detail"] == "screening_required", path
    # The pregnancy question must now be answered.
    answers = {k: v for k, v in NO_RISK.items() if k != "pregnant_or_breastfeeding"}
    assert c.post(f"{API}/profile/screening", json=answers).status_code == 422
    assert c.post(f"{API}/profile/screening", json=NO_RISK).json() == {"status": "passed"}
    assert c.get(f"{API}/nutrition/targets").json()["status"] == "ok"


def test_female_to_male_also_resets_screening(make_user):
    c = make_user()
    onboard(c, sex="female")
    r = c.put(f"{API}/profile", json=profile_payload(sex="male"))
    assert r.json()["screening_status"] is None


def test_other_profile_changes_keep_screening(make_user):
    c = make_user()
    onboard(c)
    r = c.put(f"{API}/profile", json=profile_payload(weight_kg=72, training_days=4))
    assert r.json()["screening_status"] == "passed"
    assert c.get(f"{API}/nutrition/targets").json()["status"] == "ok"
