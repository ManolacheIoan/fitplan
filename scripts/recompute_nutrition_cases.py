"""Independent recomputation of the nutrition reference cases (README, "How the formulas
were checked").

Does not import FitPlan code. It re-implements the documented pipeline from the README
with exact fractions and its own copy of the constants, then compares the results with
the values pinned in backend/tests/unit/test_nutrition_reference_cases.py.

    python3 scripts/recompute_nutrition_cases.py     # exit code 1 on any mismatch

It checks that the code computes what the formulas say. It does not validate the
formulas or the constants.
"""

import sys
from decimal import ROUND_HALF_EVEN, Decimal
from fractions import Fraction as F

# Documented constants (README "Constants that a qualified professional must validate").
SEX_CONSTANT = {"male": F(5), "female": F(-161)}
ACTIVITY = {"light": F("1.375"), "moderate": F("1.55"), "active": F("1.725")}
DEFICIT, SURPLUS = F("0.20"), F("0.10")
MAX_WEEKLY = {"lose": F("0.0075"), "gain": F("0.0025")}
KCAL_PER_KG = F(7700)
FLOOR = {"male": 1500, "female": 1200}
PROTEIN_PER_KG = {"lose": F(2), "maintain": F("1.6"), "gain": F("1.8")}
MIN_FAT_SHARE = F("0.25")
# Integer rounding used by the app for kcal (to 10), protein and fat.
ROUNDING = ROUND_HALF_EVEN


def round_int(value: F) -> int:
    return int(
        (Decimal(value.numerator) / Decimal(value.denominator)).quantize(0, ROUNDING)
    )


def compute(sex: str, age: int, height: int, weight: int, activity: str, goal: str):
    bmr = 10 * F(weight) + F("6.25") * height - 5 * age + SEX_CONSTANT[sex]
    tdee = bmr * ACTIVITY[activity]
    if goal == "maintain":
        target = tdee
    else:
        fraction = DEFICIT if goal == "lose" else SURPLUS
        cap = weight * MAX_WEEKLY[goal] * KCAL_PER_KG / 7
        change = min(tdee * fraction, cap)
        target = tdee - change if goal == "lose" else tdee + change
    target = max(target, F(FLOOR[sex]))
    kcal = round_int(target / 10) * 10
    fat = round_int(kcal * MIN_FAT_SHARE / 9)
    protein = round_int(weight * PROTEIN_PER_KG[goal])
    remaining = kcal - 9 * fat - 4 * protein
    if remaining < 0:
        protein, carbs = max(0, (kcal - 9 * fat) // 4), 0
    else:
        carbs = remaining // 4
    return bmr, tdee, kcal, protein, fat, carbs


# (inputs, expected BMR, TDEE, kcal, protein, fat, carbs), as in the README table.
CASES = {
    "A": (
        ("female", 30, 168, 70, "moderate", "lose"),
        "1439",
        "2230.45",
        1780,
        140,
        49,
        194,
    ),
    "B": (
        ("male", 25, 180, 80, "active", "gain"),
        "1805",
        "3113.625",
        3330,
        144,
        92,
        481,
    ),
    "C": (
        ("male", 45, 175, 95, "light", "maintain"),
        "1823.75",
        "2507.65625",
        2510,
        152,
        70,
        318,
    ),
}


def main() -> int:
    failures = 0
    for name, (inputs, *expected) in CASES.items():
        bmr, tdee, kcal, protein, fat, carbs = compute(*inputs)
        got = [bmr, tdee, kcal, protein, fat, carbs]
        want = [F(expected[0]), F(expected[1]), *expected[2:]]
        ok = got == want
        failures += not ok
        print(
            f"{name}: BMR {float(bmr):g}, TDEE {float(tdee):g}, {kcal} kcal, "
            f"P/F/C {protein}/{fat}/{carbs} g -> {'OK' if ok else f'MISMATCH, expected {want}'}"
        )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
