"""Training prescription constants for the rule-based plan generator.

!!! Placeholders based on commonly used general-population defaults. They must be
!!! reviewed by a qualified professional (e.g. certified coach / physiotherapist)
!!! before public use.
"""

from typing import Final

from app.plans.models import Pattern as P
from app.plans.models import Template
from app.profile.models import Experience, Goal

# --- Sets / reps / rest ----------------------------------------------------------------------
# (sets, reps_min, reps_max, rest_seconds) by goal, for compound and isolation exercises.
PRESCRIPTION: Final = {
    Goal.LOSE: {"compound": (3, 8, 12, 90), "isolation": (3, 12, 15, 60)},
    Goal.MAINTAIN: {"compound": (3, 8, 12, 90), "isolation": (3, 10, 15, 60)},
    Goal.GAIN: {"compound": (4, 6, 10, 120), "isolation": (3, 8, 12, 75)},
}
# Added to the number of sets of compound exercises (never below MIN_SETS).
SET_ADJUSTMENT: Final = {
    Experience.BEGINNER: -1,
    Experience.INTERMEDIATE: 0,
    Experience.ADVANCED: 1,
}
MIN_SETS: Final = 2
# Exercises per session; templates list slots by priority and are trimmed to this length.
MAX_EXERCISES_PER_SESSION: Final = {
    Experience.BEGINNER: 5,
    Experience.INTERMEDIATE: 6,
    Experience.ADVANCED: 7,
}

# --- Progressive overload (double progression) ---------------------------------------------
# When every set of an exercise reached reps_max, suggest adding this much weight (kg).
WEIGHT_INCREMENT_KG: Final = {"lower_compound": 5.0, "other": 2.5}
LOWER_BODY_PATTERNS: Final = {P.SQUAT, P.HINGE, P.LUNGE}

# --- Split templates ---------------------------------------------------------------------------
# Template by training days per week. Plans list one rotation of sessions; the user
# trains them in order, `days_per_week` times per week.
TEMPLATE_FOR_DAYS: Final = {
    2: Template.FULL_BODY,
    3: Template.FULL_BODY,
    4: Template.UPPER_LOWER,
    5: Template.PUSH_PULL_LEGS,
    6: Template.PUSH_PULL_LEGS,
}

_FULL_A = [
    P.SQUAT,
    P.HORIZONTAL_PUSH,
    P.VERTICAL_PULL,
    P.HINGE,
    P.SHOULDER_ISOLATION,
    P.BICEPS,
    P.CORE,
]
_FULL_B = [
    P.HINGE,
    P.VERTICAL_PUSH,
    P.HORIZONTAL_PULL,
    P.LUNGE,
    P.CHEST_ISOLATION,
    P.TRICEPS,
    P.CORE,
]
_FULL_C = [
    P.SQUAT,
    P.HORIZONTAL_PUSH,
    P.HORIZONTAL_PULL,
    P.LUNGE,
    P.HAMSTRING_ISOLATION,
    P.SHOULDER_ISOLATION,
    P.CORE,
]
_UPPER_A = [
    P.HORIZONTAL_PUSH,
    P.HORIZONTAL_PULL,
    P.VERTICAL_PUSH,
    P.VERTICAL_PULL,
    P.SHOULDER_ISOLATION,
    P.BICEPS,
    P.TRICEPS,
]
_UPPER_B = [
    P.VERTICAL_PULL,
    P.HORIZONTAL_PUSH,
    P.HORIZONTAL_PULL,
    P.VERTICAL_PUSH,
    P.CHEST_ISOLATION,
    P.TRICEPS,
    P.BICEPS,
]
_LOWER_A = [P.SQUAT, P.HINGE, P.LUNGE, P.QUAD_ISOLATION, P.HAMSTRING_ISOLATION, P.CALVES, P.CORE]
_LOWER_B = [P.HINGE, P.SQUAT, P.GLUTE_ISOLATION, P.LUNGE, P.HAMSTRING_ISOLATION, P.CALVES, P.CORE]
_PUSH_A = [
    P.HORIZONTAL_PUSH,
    P.VERTICAL_PUSH,
    P.HORIZONTAL_PUSH,
    P.SHOULDER_ISOLATION,
    P.TRICEPS,
    P.CHEST_ISOLATION,
    P.TRICEPS,
]
_PUSH_B = [
    P.VERTICAL_PUSH,
    P.HORIZONTAL_PUSH,
    P.HORIZONTAL_PUSH,
    P.SHOULDER_ISOLATION,
    P.TRICEPS,
    P.CHEST_ISOLATION,
    P.CORE,
]
_PULL_A = [
    P.VERTICAL_PULL,
    P.HORIZONTAL_PULL,
    P.HORIZONTAL_PULL,
    P.SHOULDER_ISOLATION,
    P.BICEPS,
    P.BICEPS,
    P.CORE,
]
_PULL_B = [
    P.HORIZONTAL_PULL,
    P.VERTICAL_PULL,
    P.VERTICAL_PULL,
    P.SHOULDER_ISOLATION,
    P.BICEPS,
    P.BICEPS,
    P.CORE,
]
_LEGS_A = _LOWER_A
_LEGS_B = _LOWER_B

# (day name, slots by priority) per template and days per week.
SESSIONS: Final[dict[int, list[tuple[str, list[P]]]]] = {
    2: [("Corp întreg A", _FULL_A), ("Corp întreg B", _FULL_B)],
    3: [("Corp întreg A", _FULL_A), ("Corp întreg B", _FULL_B), ("Corp întreg C", _FULL_C)],
    4: [
        ("Superior A", _UPPER_A),
        ("Inferior A", _LOWER_A),
        ("Superior B", _UPPER_B),
        ("Inferior B", _LOWER_B),
    ],
    5: [
        ("Împingere A", _PUSH_A),
        ("Tracțiune A", _PULL_A),
        ("Picioare A", _LEGS_A),
        ("Împingere B", _PUSH_B),
        ("Tracțiune B", _PULL_B),
        ("Picioare B", _LEGS_B),
    ],
}
SESSIONS[6] = SESSIONS[5]
