"""Expected values are computed by hand from the documented formulas."""

import pytest

from app.common import health_constants as hc
from app.nutrition.rules import (
    NutritionInput,
    bmr_mifflin_st_jeor,
    compute_targets,
    energy_target,
    macros,
    max_daily_adjustment,
    round_half_up,
    tdee,
)
from app.profile.models import ActivityLevel, Goal, Sex


def make(**overrides: object) -> NutritionInput:
    data: dict[str, object] = {
        "sex": Sex.FEMALE,
        "age_years": 30,
        "height_cm": 168.0,
        "weight_kg": 70.0,
        "activity_level": ActivityLevel.MODERATE,
        "goal": Goal.LOSE,
    }
    return NutritionInput(**{**data, **overrides})  # type: ignore[arg-type]


def test_bmr_mifflin_st_jeor():
    # 10*70 + 6.25*168 - 5*30 - 161 = 1439
    assert bmr_mifflin_st_jeor(Sex.FEMALE, 30, 168, 70) == pytest.approx(1439)
    # 10*80 + 6.25*180 - 5*25 + 5 = 1805
    assert bmr_mifflin_st_jeor(Sex.MALE, 25, 180, 80) == pytest.approx(1805)


@pytest.mark.parametrize("level", list(ActivityLevel))
def test_tdee_uses_activity_multiplier(level: ActivityLevel):
    assert tdee(1000, level) == pytest.approx(1000 * hc.ACTIVITY_MULTIPLIERS[level.value])


def test_moderate_deficit_for_weight_loss():
    t = compute_targets(make())
    # TDEE = 1439 * 1.55 = 2230.45; deficit = 20% = 446.09 (< cap 577.5) -> 1784.36 -> 1780
    assert (t.bmr_kcal, t.tdee_kcal, t.kcal) == (1439, 2230, 1780)
    # protein 2.0 g/kg * 70 = 140; fat 25% of 1780 / 9 = 49; carbs (1780-441-560)/4 = 194
    assert (t.protein_g, t.fat_g, t.carbs_g) == (140, 49, 194)
    assert t.weekly_change_kg == pytest.approx(-0.41)
    assert not t.floor_applied


def test_surplus_for_muscle_gain_is_capped_by_weekly_rate():
    t = compute_targets(
        make(
            sex=Sex.MALE,
            age_years=25,
            height_cm=180,
            weight_kg=80,
            activity_level=ActivityLevel.ACTIVE,
            goal=Goal.GAIN,
        )
    )
    # TDEE = 1805 * 1.725 = 3113.6; 10% = 311.4 > cap 80*0.0025*7700/7 = 220 -> 3333.6 -> 3330
    assert (t.tdee_kcal, t.kcal) == (3114, 3330)
    assert t.weekly_change_kg == pytest.approx(0.2, abs=0.01)


def test_maintenance_equals_tdee():
    t = compute_targets(make(goal=Goal.MAINTAIN))
    assert t.kcal == 2230
    assert t.weekly_change_kg == pytest.approx(0, abs=0.01)


def test_deficit_capped_by_max_weekly_loss():
    tdee_kcal, weight = 3200.0, 60.0
    cap = max_daily_adjustment(weight, Goal.LOSE)
    assert cap == pytest.approx(60 * 0.0075 * 7700 / 7)  # 495
    assert energy_target(tdee_kcal, weight, Goal.LOSE) == pytest.approx(tdee_kcal - cap)
    weekly_loss_kg = cap * 7 / hc.KCAL_PER_KG_BODY_MASS
    assert weekly_loss_kg <= weight * hc.MAX_WEEKLY_LOSS_FRACTION + 1e-9


@pytest.mark.parametrize(("sex", "floor"), [(Sex.FEMALE, 1200), (Sex.MALE, 1500)])
def test_calorie_floor_is_enforced(sex: Sex, floor: int):
    t = compute_targets(
        make(
            sex=sex,
            age_years=60,
            height_cm=150,
            weight_kg=45,
            activity_level=ActivityLevel.SEDENTARY,
        )
    )
    assert t.kcal == floor
    assert t.floor_applied


def test_fat_never_below_minimum_share():
    for goal in Goal:
        t = compute_targets(make(goal=goal))
        assert t.fat_g * hc.KCAL_PER_G_FAT >= t.kcal * hc.MIN_FAT_FRACTION - hc.KCAL_PER_G_FAT


def test_macro_calories_do_not_exceed_target():
    for goal in Goal:
        t = compute_targets(make(goal=goal))
        total = t.protein_g * 4 + t.fat_g * 9 + t.carbs_g * 4
        assert t.kcal - 4 <= total <= t.kcal


def test_protein_reduced_when_it_would_exceed_calories():
    protein, fat, carbs = macros(1200, 150, Goal.LOSE)
    # fat = 33 g (297 kcal); protein limited to (1200 - 297) // 4 = 225 g; no carbohydrates
    assert (protein, fat, carbs) == (225, 33, 0)


def test_floor_can_raise_a_weight_loss_target_above_maintenance():
    # BMR = 450 + 937.5 - 300 - 161 = 926.5; TDEE = 926.5 * 1.2 = 1111.8 < 1200 floor.
    t = compute_targets(
        make(
            sex=Sex.FEMALE,
            age_years=60,
            height_cm=150,
            weight_kg=45,
            activity_level=ActivityLevel.SEDENTARY,
            goal=Goal.LOSE,
        )
    )
    assert (t.tdee_kcal, t.kcal, t.floor_applied) == (1112, 1200, True)
    assert t.kcal > t.tdee_kcal
    # The estimate honestly shows a gain, not a loss: (1200 - 1111.8) * 7 / 7700 = 0.08 kg.
    assert t.weekly_change_kg == pytest.approx(0.08)
    # Macros are computed from the floor-raised target: fat 33 g, protein 90 g, carbs 135 g.
    assert (t.protein_g, t.fat_g, t.carbs_g) == (90, 33, 135)


@pytest.mark.parametrize(("value", "expected"), [(92.5, 93), (49.5, 50), (49.4, 49), (0.5, 1)])
def test_macros_round_half_up(value: float, expected: int):
    assert round_half_up(value) == expected


def test_fat_half_gram_is_rounded_up():
    # 3330 kcal * 25 % / 9 = 92.5 g; half to even would give 92.
    assert macros(3330, 80, Goal.GAIN)[1] == 93
