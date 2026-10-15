"""Safety screening rules (pure functions, no I/O).

Thresholds live in app/common/health_constants.py and must be validated by a
qualified professional.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.common.health_constants import BMI_MIN_FOR_WEIGHT_LOSS
from app.profile.models import Goal, ScreeningStatus


@dataclass(frozen=True)
class ScreeningAnswers:
    pregnant_or_breastfeeding: bool
    diagnosed_medical_condition: bool
    eating_disorder_history: bool
    current_injury: bool


def evaluate(answers: ScreeningAnswers) -> ScreeningStatus:
    """Any "yes" means: generate nothing and recommend a professional."""
    any_yes = (
        answers.pregnant_or_breastfeeding
        or answers.diagnosed_medical_condition
        or answers.eating_disorder_history
        or answers.current_injury
    )
    return ScreeningStatus.REFER if any_yes else ScreeningStatus.PASSED


def age_on(birth_date: date, today: date) -> int:
    had_birthday = (today.month, today.day) >= (birth_date.month, birth_date.day)
    return today.year - birth_date.year - (0 if had_birthday else 1)


def bmi(weight_kg: Decimal | float, height_cm: Decimal | float) -> float:
    height_m = float(height_cm) / 100
    return float(weight_kg) / (height_m * height_m)


def weight_loss_allowed(weight_kg: Decimal | float, height_cm: Decimal | float) -> bool:
    return bmi(weight_kg, height_cm) >= BMI_MIN_FOR_WEIGHT_LOSS


def goal_allowed(goal: Goal, weight_kg: Decimal | float, height_cm: Decimal | float) -> bool:
    return goal is not Goal.LOSE or weight_loss_allowed(weight_kg, height_cm)
