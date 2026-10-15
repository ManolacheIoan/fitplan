"""Training prescription constants for the rule-based plan generator.

!!! Placeholders based on commonly used general-population defaults. They must be
!!! reviewed by a qualified professional (e.g. certified coach / physiotherapist)
!!! before public use.
"""

from typing import Final

from app.plans.models import Pattern as P
from app.plans.models import RepScheme, Template
from app.profile.models import Experience, Goal

# --- Sets / reps / rest ----------------------------------------------------------------------
# (sets, reps_min, reps_max, rest_seconds) per rep scheme and goal. For TIMED the "reps"
# are seconds held.
_ALL_GOALS = (Goal.LOSE, Goal.MAINTAIN, Goal.GAIN)
PRESCRIPTION: Final[dict[RepScheme, dict[Goal, tuple[int, int, int, int]]]] = {
    RepScheme.STRENGTH: {
        Goal.LOSE: (3, 6, 10, 120),
        Goal.MAINTAIN: (3, 6, 10, 120),
        Goal.GAIN: (4, 5, 8, 150),
    },
    RepScheme.COMPOUND: {
        Goal.LOSE: (3, 8, 12, 90),
        Goal.MAINTAIN: (3, 8, 12, 90),
        Goal.GAIN: (4, 8, 12, 90),
    },
    RepScheme.ISOLATION: {
        Goal.LOSE: (3, 12, 15, 60),
        Goal.MAINTAIN: (3, 10, 15, 60),
        Goal.GAIN: (3, 10, 15, 60),
    },
    RepScheme.BODYWEIGHT_HARD: dict.fromkeys(_ALL_GOALS, (3, 5, 10, 90)),
    RepScheme.CALVES: dict.fromkeys(_ALL_GOALS, (3, 12, 20, 60)),
    RepScheme.CORE: dict.fromkeys(_ALL_GOALS, (3, 10, 15, 45)),
    RepScheme.TIMED: dict.fromkeys(_ALL_GOALS, (3, 20, 45, 45)),
}
# Experience changes the number of sets of these schemes (never below MIN_SETS).
SET_ADJUSTED_SCHEMES: Final = {RepScheme.STRENGTH, RepScheme.COMPOUND}
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
# Training days per week each program supports. The plan has exactly that many days.
ALLOWED_DAYS: Final = {
    Template.FULL_BODY: {2, 3},
    Template.UPPER_LOWER: {2, 4},
    Template.PUSH_PULL_LEGS: {3, 5, 6},
    Template.BRO_SPLIT: {5},
}
# Program used when the user chooses "auto".
AUTO_TEMPLATE: Final = {
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
# Bro split: one muscle group per day. Lists are longer than the session size so that
# every experience level fills its sessions even when a pattern has few options.
_CHEST = [
    P.HORIZONTAL_PUSH,
    P.HORIZONTAL_PUSH,
    P.CHEST_ISOLATION,
    P.HORIZONTAL_PUSH,
    P.CHEST_ISOLATION,
    P.TRICEPS,
    P.CORE,
    P.CORE,
]
_BACK = [
    P.VERTICAL_PULL,
    P.HORIZONTAL_PULL,
    P.HORIZONTAL_PULL,
    P.VERTICAL_PULL,
    P.HINGE,
    P.SHOULDER_ISOLATION,
    P.CORE,
    P.CORE,
]
_SHOULDERS = [
    P.VERTICAL_PUSH,
    P.SHOULDER_ISOLATION,
    P.SHOULDER_ISOLATION,
    P.VERTICAL_PUSH,
    P.SHOULDER_ISOLATION,
    P.TRICEPS,
    P.CORE,
    P.CORE,
]
_LEGS_BRO = [
    P.SQUAT,
    P.HINGE,
    P.LUNGE,
    P.QUAD_ISOLATION,
    P.HAMSTRING_ISOLATION,
    P.CALVES,
    P.GLUTE_ISOLATION,
    P.CORE,
]
_ARMS = [P.BICEPS, P.TRICEPS, P.BICEPS, P.TRICEPS, P.BICEPS, P.TRICEPS, P.CORE, P.CORE]

Session = tuple[str, list[P]]

# (day name, slots by priority) for each program and number of training days.
SESSIONS: Final[dict[tuple[Template, int], list[Session]]] = {
    (Template.FULL_BODY, 2): [("Corp întreg A", _FULL_A), ("Corp întreg B", _FULL_B)],
    (Template.FULL_BODY, 3): [
        ("Corp întreg A", _FULL_A),
        ("Corp întreg B", _FULL_B),
        ("Corp întreg C", _FULL_C),
    ],
    (Template.UPPER_LOWER, 2): [("Superior", _UPPER_A), ("Inferior", _LOWER_A)],
    (Template.UPPER_LOWER, 4): [
        ("Superior A", _UPPER_A),
        ("Inferior A", _LOWER_A),
        ("Superior B", _UPPER_B),
        ("Inferior B", _LOWER_B),
    ],
    (Template.PUSH_PULL_LEGS, 3): [
        ("Împingere", _PUSH_A),
        ("Tracțiune", _PULL_A),
        ("Picioare", _LEGS_A),
    ],
    (Template.PUSH_PULL_LEGS, 5): [
        ("Împingere", _PUSH_A),
        ("Tracțiune", _PULL_A),
        ("Picioare", _LEGS_A),
        ("Superior", _UPPER_B),
        ("Inferior", _LOWER_B),
    ],
    (Template.PUSH_PULL_LEGS, 6): [
        ("Împingere A", _PUSH_A),
        ("Tracțiune A", _PULL_A),
        ("Picioare A", _LEGS_A),
        ("Împingere B", _PUSH_B),
        ("Tracțiune B", _PULL_B),
        ("Picioare B", _LEGS_B),
    ],
    (Template.BRO_SPLIT, 5): [
        ("Piept", _CHEST),
        ("Spate", _BACK),
        ("Umeri", _SHOULDERS),
        ("Picioare", _LEGS_BRO),
        ("Brațe", _ARMS),
    ],
}
