"""Reference cases recomputed independently (exact fractions, without FitPlan code).

The same cases are listed in the README ("How I validated the formulas") so they can be
compared with a public Mifflin-St Jeor calculator (not done yet).
"""

import pytest

from app.nutrition.rules import NutritionInput, compute_targets
from app.profile.models import ActivityLevel, Goal, Sex

CASES = [
    # (inputs, BMR, TDEE, kcal, protein, fat, carbs)
    (
        NutritionInput(Sex.FEMALE, 30, 168, 70, ActivityLevel.MODERATE, Goal.LOSE),
        1439,
        2230,
        1780,
        140,
        49,
        194,
    ),
    (
        NutritionInput(Sex.MALE, 25, 180, 80, ActivityLevel.ACTIVE, Goal.GAIN),
        1805,
        3114,
        3330,
        144,
        93,  # 92.5 rounded half up
        479,
    ),
    (
        NutritionInput(Sex.MALE, 45, 175, 95, ActivityLevel.LIGHT, Goal.MAINTAIN),
        1824,
        2508,
        2510,
        152,
        70,
        318,
    ),
]


@pytest.mark.parametrize(("data", "bmr", "tdee", "kcal", "protein", "fat", "carbs"), CASES)
def test_reference_case(data, bmr, tdee, kcal, protein, fat, carbs):
    t = compute_targets(data)
    assert (t.bmr_kcal, t.tdee_kcal, t.kcal) == (bmr, tdee, kcal)
    assert (t.protein_g, t.fat_g, t.carbs_g) == (protein, fat, carbs)
