"""Simple progressive-overload suggestions (double progression). Pure functions."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from app.plans import constants as c
from app.plans.models import Pattern


@dataclass(frozen=True)
class LoggedSet:
    weight_kg: Decimal
    reps: int


@dataclass(frozen=True)
class Suggestion:
    kind: Literal["first_time", "add_weight", "add_reps"]
    weight_kg: Decimal | None


def increment_for(pattern: Pattern, is_compound: bool) -> Decimal:
    key = "lower_compound" if is_compound and pattern in c.LOWER_BODY_PATTERNS else "other"
    return Decimal(str(c.WEIGHT_INCREMENT_KG[key]))


def suggest(
    last_sets: list[LoggedSet], reps_max: int, pattern: Pattern, is_compound: bool
) -> Suggestion:
    """Suggest the next step based on the sets logged the last time.

    - never done: pick a weight that allows reps_max with good technique;
    - every set reached reps_max: add weight (and restart from reps_min);
    - otherwise: keep the weight and aim for more repetitions.
    """
    if not last_sets:
        return Suggestion("first_time", None)
    top_weight = max(s.weight_kg for s in last_sets)
    if all(s.reps >= reps_max for s in last_sets if s.weight_kg == top_weight):
        return Suggestion("add_weight", top_weight + increment_for(pattern, is_compound))
    return Suggestion("add_reps", top_weight)
