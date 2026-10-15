from collections import Counter

import pytest

from app.plans import constants as c
from app.plans.generator import generate, resolve_template
from app.plans.models import Exercise, Pattern, Template
from app.profile.models import Experience, Goal, Program
from seed.exercises import EXERCISES

LEVEL = {"beginner": 0, "intermediate": 1, "advanced": 2}


@pytest.fixture(scope="module")
def library() -> list[Exercise]:
    return [
        Exercise(
            id=i,
            slug=slug,
            name=name,
            pattern=pattern,
            primary_muscle=primary,
            secondary_muscles=secondary,
            equipment=equipment,
            difficulty=difficulty,
            is_compound=compound,
            description=description,
        )
        for i, (
            slug,
            name,
            pattern,
            primary,
            secondary,
            equipment,
            difficulty,
            compound,
            description,
        ) in enumerate(EXERCISES, start=1)
    ]


def test_library_size_and_unique_slugs():
    assert 60 <= len(EXERCISES) <= 80
    assert len({e[0] for e in EXERCISES}) == len(EXERCISES)


COMBOS = sorted(c.SESSIONS, key=lambda k: (k[0].value, k[1]))


def auto(days: int) -> Template:
    return c.AUTO_TEMPLATE[days]


@pytest.mark.parametrize(
    ("days", "template"),
    [
        (2, Template.FULL_BODY),
        (3, Template.FULL_BODY),
        (4, Template.UPPER_LOWER),
        (5, Template.PUSH_PULL_LEGS),
        (6, Template.PUSH_PULL_LEGS),
    ],
)
def test_auto_program_by_days_per_week(days, template):
    assert resolve_template(Program.AUTO, days) is template


def test_explicit_program_only_for_supported_days():
    assert resolve_template(Program.BRO_SPLIT, 5) is Template.BRO_SPLIT
    assert resolve_template(Program.BRO_SPLIT, 4) is None
    assert resolve_template(Program.PUSH_PULL_LEGS, 3) is Template.PUSH_PULL_LEGS
    assert resolve_template(Program.PUSH_PULL_LEGS, 4) is None
    assert resolve_template(Program.UPPER_LOWER, 2) is Template.UPPER_LOWER
    assert resolve_template(Program.FULL_BODY, 5) is None
    for template, days in c.SESSIONS:
        assert days in c.ALLOWED_DAYS[template]


@pytest.mark.parametrize(("template", "days"), COMBOS)
def test_plan_has_exactly_one_day_per_training_day(library, template, days):
    plan = generate(library, template, days, Goal.MAINTAIN, Experience.INTERMEDIATE)
    assert plan.template is template
    assert len(plan.days) == days
    assert len({d.name for d in plan.days}) == days


@pytest.mark.parametrize("experience", list(Experience))
@pytest.mark.parametrize(("template", "days"), COMBOS)
def test_sessions_respect_experience(library, template, days, experience):
    plan = generate(library, template, days, Goal.GAIN, experience)
    for day in plan.days:
        assert len(day.exercises) == c.MAX_EXERCISES_PER_SESSION[experience]
        ids = [p.exercise.id for p in day.exercises]
        assert len(ids) == len(set(ids)), "no exercise twice in a session"
        for p in day.exercises:
            assert LEVEL[p.exercise.difficulty] <= LEVEL[experience]


def test_beginner_gets_only_beginner_exercises(library):
    plan = generate(library, auto(3), 3, Goal.LOSE, Experience.BEGINNER)
    assert {p.exercise.difficulty for d in plan.days for p in d.exercises} == {"beginner"}


@pytest.mark.parametrize("goal", list(Goal))
def test_sets_reps_rest_follow_goal_and_experience(library, goal):
    for experience in Experience:
        plan = generate(library, auto(4), 4, goal, experience)
        for day in plan.days:
            for p in day.exercises:
                role = "compound" if p.exercise.is_compound else "isolation"
                sets, reps_min, reps_max, rest = c.PRESCRIPTION[goal][role]
                if p.exercise.is_compound:
                    sets = max(c.MIN_SETS, sets + c.SET_ADJUSTMENT[experience])
                assert (p.sets, p.reps_min, p.reps_max, p.rest_seconds) == (
                    sets,
                    reps_min,
                    reps_max,
                    rest,
                )


def test_repeated_patterns_rotate_exercises(library):
    plan = generate(library, auto(3), 3, Goal.MAINTAIN, Experience.ADVANCED)
    squats = [
        p.exercise.slug for d in plan.days for p in d.exercises if p.exercise.pattern == "squat"
    ]
    assert len(squats) == 2 and squats[0] != squats[1]


def test_generation_is_deterministic(library):
    a = generate(library, auto(5), 5, Goal.GAIN, Experience.INTERMEDIATE)
    b = generate(library, auto(5), 5, Goal.GAIN, Experience.INTERMEDIATE)
    assert a == b


def test_weekly_volume_is_balanced_between_push_and_pull(library):
    plan = generate(library, auto(4), 4, Goal.GAIN, Experience.ADVANCED)
    patterns = Counter(p.exercise.pattern for d in plan.days for p in d.exercises)
    push = patterns[Pattern.HORIZONTAL_PUSH] + patterns[Pattern.VERTICAL_PUSH]
    pull = patterns[Pattern.HORIZONTAL_PULL] + patterns[Pattern.VERTICAL_PULL]
    assert push == pull
