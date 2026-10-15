"""Rule-based plan generator (no AI). Pure: takes the exercise library as input."""

from collections import defaultdict
from dataclasses import dataclass

from app.plans import constants as c
from app.plans.models import Exercise, Pattern, Template
from app.profile.models import Experience, Goal, Program

_LEVEL = {Experience.BEGINNER: 0, Experience.INTERMEDIATE: 1, Experience.ADVANCED: 2}


@dataclass(frozen=True)
class Prescription:
    exercise: Exercise
    sets: int
    reps_min: int
    reps_max: int
    rest_seconds: int


@dataclass(frozen=True)
class GeneratedDay:
    name: str
    exercises: list[Prescription]


@dataclass(frozen=True)
class GeneratedPlan:
    template: Template
    days: list[GeneratedDay]


def candidates_by_pattern(
    library: list[Exercise], experience: Experience
) -> dict[Pattern, list[Exercise]]:
    """Exercises allowed for the experience level, closest difficulty first."""
    level = _LEVEL[experience]
    grouped: dict[Pattern, list[Exercise]] = defaultdict(list)
    for exercise in library:
        if _LEVEL[exercise.difficulty] <= level:
            grouped[exercise.pattern].append(exercise)
    for options in grouped.values():
        options.sort(key=lambda e: (-_LEVEL[e.difficulty], e.slug))
    return grouped


def prescription(exercise: Exercise, goal: Goal, experience: Experience) -> Prescription:
    sets, reps_min, reps_max, rest = c.PRESCRIPTION[exercise.rep_scheme][goal]
    if exercise.rep_scheme in c.SET_ADJUSTED_SCHEMES:
        sets = max(c.MIN_SETS, sets + c.SET_ADJUSTMENT[experience])
    return Prescription(exercise, sets, reps_min, reps_max, rest)


def resolve_template(program: Program, days_per_week: int) -> Template | None:
    """Template for the chosen program, or None if it does not support that many days."""
    if program is Program.AUTO:
        return c.AUTO_TEMPLATE[days_per_week]
    template = Template(program.value)
    return template if days_per_week in c.ALLOWED_DAYS[template] else None


def generate(
    library: list[Exercise],
    template: Template,
    days_per_week: int,
    goal: Goal,
    experience: Experience,
) -> GeneratedPlan:
    """One plan day per training day, following the template's sessions."""
    options = candidates_by_pattern(library, experience)
    # Rotating through candidates gives variety when a pattern appears several times.
    next_index: dict[Pattern, int] = defaultdict(int)
    max_per_session = c.MAX_EXERCISES_PER_SESSION[experience]
    days = []
    for name, slots in c.SESSIONS[(template, days_per_week)]:
        chosen: list[Prescription] = []
        used: set[int] = set()
        for pattern in slots:
            if len(chosen) == max_per_session:
                break
            pool = options.get(pattern, [])
            for _ in range(len(pool)):
                exercise = pool[next_index[pattern] % len(pool)]
                next_index[pattern] += 1
                if exercise.id not in used:
                    used.add(exercise.id)
                    chosen.append(prescription(exercise, goal, experience))
                    break
        days.append(GeneratedDay(name, chosen))
    return GeneratedPlan(template, days)
