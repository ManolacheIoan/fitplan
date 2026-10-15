from dataclasses import replace
from datetime import date

import pytest

from app.common.health_constants import BMI_MIN_FOR_WEIGHT_LOSS
from app.profile.models import Goal, ScreeningStatus
from app.profile.screening import ScreeningAnswers, age_on, bmi, evaluate, goal_allowed

ALL_NO = ScreeningAnswers(False, False, False, False)


def test_all_no_passes():
    assert evaluate(ALL_NO) is ScreeningStatus.PASSED


@pytest.mark.parametrize(
    "field",
    [
        "pregnant_or_breastfeeding",
        "diagnosed_medical_condition",
        "eating_disorder_history",
        "current_injury",
    ],
)
def test_any_yes_refers_to_professional(field: str):
    assert evaluate(replace(ALL_NO, **{field: True})) is ScreeningStatus.REFER


@pytest.mark.parametrize(
    ("birth", "today", "expected"),
    [
        (date(2000, 6, 15), date(2018, 6, 14), 17),
        (date(2000, 6, 15), date(2018, 6, 15), 18),
        (date(2000, 2, 29), date(2018, 2, 28), 17),
        (date(2000, 2, 29), date(2018, 3, 1), 18),
    ],
)
def test_age_on_birthday_boundaries(birth: date, today: date, expected: int):
    assert age_on(birth, today) == expected


def test_bmi():
    assert bmi(70, 175) == pytest.approx(22.857, abs=0.001)


def test_weight_loss_blocked_below_bmi_threshold():
    height = 170
    at_threshold = BMI_MIN_FOR_WEIGHT_LOSS * (height / 100) ** 2
    assert goal_allowed(Goal.LOSE, at_threshold, height)
    assert not goal_allowed(Goal.LOSE, at_threshold - 0.1, height)
    # Other goals are not affected by the threshold.
    assert goal_allowed(Goal.MAINTAIN, at_threshold - 5, height)
    assert goal_allowed(Goal.GAIN, at_threshold - 5, height)
