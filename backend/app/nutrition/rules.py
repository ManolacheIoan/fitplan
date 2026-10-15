"""Deterministic nutrition estimates (no AI). Pure functions, fully unit-tested.

Pipeline:
1. BMR with the Mifflin-St Jeor equation.
2. TDEE = BMR * activity multiplier.
3. Energy target: TDEE minus a moderate deficit (lose) or plus a surplus (gain).
   The deficit/surplus is capped so the estimated weekly change of body weight stays
   within MAX_WEEKLY_*_FRACTION of body weight.
4. Calorie floor: the target never goes below CALORIE_FLOOR for the given sex.
5. Macros: protein = g/kg * body weight; fat = at least MIN_FAT_FRACTION of calories;
   carbohydrates = the remaining calories. If protein + minimum fat exceed the target,
   protein is reduced first and carbohydrates become 0.

All results are approximate estimates. Every constant is in
app/common/health_constants.py and must be validated by a qualified professional.
"""

from dataclasses import dataclass

from app.common import health_constants as hc
from app.profile.models import ActivityLevel, Goal, Sex

# Increment whenever a formula or constant changes, so stored targets can be traced.
RULES_VERSION = 1


@dataclass(frozen=True)
class NutritionInput:
    sex: Sex
    age_years: int
    height_cm: float
    weight_kg: float
    activity_level: ActivityLevel
    goal: Goal


@dataclass(frozen=True)
class Targets:
    bmr_kcal: int
    tdee_kcal: int
    kcal: int
    protein_g: int
    fat_g: int
    carbs_g: int
    # Estimated weekly change of body weight in kg (negative = loss). Approximate.
    weekly_change_kg: float
    floor_applied: bool


def bmr_mifflin_st_jeor(sex: Sex, age_years: int, height_cm: float, weight_kg: float) -> float:
    return (
        hc.MIFFLIN_WEIGHT_COEF * weight_kg
        + hc.MIFFLIN_HEIGHT_COEF * height_cm
        - hc.MIFFLIN_AGE_COEF * age_years
        + hc.MIFFLIN_SEX_CONSTANT[sex.value]
    )


def tdee(bmr: float, activity_level: ActivityLevel) -> float:
    return bmr * hc.ACTIVITY_MULTIPLIERS[activity_level.value]


def max_daily_adjustment(weight_kg: float, goal: Goal) -> float:
    """Largest daily deficit/surplus (kcal) allowed by the weekly-rate cap."""
    fraction = hc.MAX_WEEKLY_LOSS_FRACTION if goal is Goal.LOSE else hc.MAX_WEEKLY_GAIN_FRACTION
    return weight_kg * fraction * hc.KCAL_PER_KG_BODY_MASS / 7


def energy_target(tdee_kcal: float, weight_kg: float, goal: Goal) -> float:
    if goal is Goal.LOSE:
        deficit = min(tdee_kcal * hc.DEFICIT_FRACTION, max_daily_adjustment(weight_kg, goal))
        return tdee_kcal - deficit
    if goal is Goal.GAIN:
        surplus = min(tdee_kcal * hc.SURPLUS_FRACTION, max_daily_adjustment(weight_kg, goal))
        return tdee_kcal + surplus
    return tdee_kcal


def apply_floor(kcal: float, sex: Sex) -> tuple[float, bool]:
    floor = hc.CALORIE_FLOOR[sex.value]
    return (float(floor), True) if kcal < floor else (kcal, False)


def macros(kcal: int, weight_kg: float, goal: Goal) -> tuple[int, int, int]:
    """Return (protein_g, fat_g, carbs_g) for a calorie target."""
    fat_g = round(kcal * hc.MIN_FAT_FRACTION / hc.KCAL_PER_G_FAT)
    protein_g = round(weight_kg * hc.PROTEIN_G_PER_KG[goal.value])
    remaining = kcal - fat_g * hc.KCAL_PER_G_FAT - protein_g * hc.KCAL_PER_G_PROTEIN
    if remaining < 0:
        # Protein + minimum fat exceed the target: reduce protein, no carbohydrates left.
        protein_g = max(0, int((kcal - fat_g * hc.KCAL_PER_G_FAT) // hc.KCAL_PER_G_PROTEIN))
        return protein_g, fat_g, 0
    return protein_g, fat_g, int(remaining // hc.KCAL_PER_G_CARB)


def compute_targets(data: NutritionInput) -> Targets:
    bmr = bmr_mifflin_st_jeor(data.sex, data.age_years, data.height_cm, data.weight_kg)
    daily = tdee(bmr, data.activity_level)
    target, floor_applied = apply_floor(energy_target(daily, data.weight_kg, data.goal), data.sex)
    kcal = round(target / 10) * 10
    protein_g, fat_g, carbs_g = macros(kcal, data.weight_kg, data.goal)
    weekly_change = (kcal - daily) * 7 / hc.KCAL_PER_KG_BODY_MASS
    return Targets(
        bmr_kcal=round(bmr),
        tdee_kcal=round(daily),
        kcal=kcal,
        protein_g=protein_g,
        fat_g=fat_g,
        carbs_g=carbs_g,
        weekly_change_kg=round(weekly_change, 2),
        floor_applied=floor_applied,
    )
