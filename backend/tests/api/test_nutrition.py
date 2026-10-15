from tests.factories import API, NO_RISK, onboard, profile_payload


def test_targets_require_completed_onboarding(make_user):
    c = make_user()
    assert c.get(f"{API}/nutrition/targets").json()["detail"] == "profile_missing"
    c.put(f"{API}/profile", json=profile_payload())
    assert c.get(f"{API}/nutrition/targets").json()["detail"] == "screening_required"


def test_targets_generated_after_passed_screening(make_user):
    c = make_user()
    onboard(c)
    body = c.get(f"{API}/nutrition/targets").json()
    assert body["status"] == "ok"
    assert body["targets"]["kcal"] > 0
    assert body["targets"]["based_on_weight_kg"] == "70.0"


def test_no_targets_after_screening_refer(make_user):
    c = make_user()
    onboard(c)
    c.post(f"{API}/profile/screening", json={**NO_RISK, "eating_disorder_history": True})
    r = c.get(f"{API}/nutrition/targets")
    assert r.status_code == 403
    assert r.json()["detail"] == "professional_advice_recommended"
    assert c.get(f"{API}/account/export").json()["nutrition_targets"] is None


def test_targets_recomputed_when_profile_changes(make_user):
    c = make_user()
    onboard(c)
    before = c.get(f"{API}/nutrition/targets").json()["targets"]["kcal"]
    c.put(f"{API}/profile", json=profile_payload(goal="gain"))
    after = c.get(f"{API}/nutrition/targets").json()["targets"]["kcal"]
    assert after > before
