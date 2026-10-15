from collections import Counter

import pytest

from app.plans import constants as c
from app.plans.generator import generate
from app.plans.models import Exercise, Pattern, Template
from app.profile.models import Experience, Goal
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


@pytest.mark.parametrize(
    ("days", "template", "sessions"),
    [
        (2, Template.FULL_BODY, 2),
        (3, Template.FULL_BODY, 3),
        (4, Template.UPPER_LOWER, 4),
        (5, Template.PUSH_PULL_LEGS, 6),
        (6, Template.PUSH_PULL_LEGS, 6),
    ],
)
def test_template_by_days_per_week(library, days, template, sessions):
    plan = generate(library, days, Goal.MAINTAIN, Experience.INTERMEDIATE)
    assert plan.template is template
    assert len(plan.days) == sessions


@pytest.mark.parametrize("experience", list(Experience))
@pytest.mark.parametrize("days", [2, 3, 4, 5, 6])
def test_sessions_respect_experience(library, days, experience):
    plan = generate(library, days, Goal.GAIN, experience)
    for day in plan.days:
        assert len(day.exercises) == c.MAX_EXERCISES_PER_SESSION[experience]
        ids = [p.exercise.id for p in day.exercises]
        assert len(ids) == len(set(ids)), "no exercise twice in a session"
        for p in day.exercises:
            assert LEVEL[p.exercise.difficulty] <= LEVEL[experience]


def test_beginner_gets_only_beginner_exercises(library):
    plan = generate(library, 3, Goal.LOSE, Experience.BEGINNER)
    assert {p.exercise.difficulty for d in plan.days for p in d.exercises} == {"beginner"}


@pytest.mark.parametrize("goal", list(Goal))
def test_sets_reps_rest_follow_goal_and_experience(library, goal):
    for experience in Experience:
        plan = generate(library, 4, goal, experience)
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
    plan = generate(library, 3, Goal.MAINTAIN, Experience.ADVANCED)
    squats = [
        p.exercise.slug for d in plan.days for p in d.exercises if p.exercise.pattern == "squat"
    ]
    assert len(squats) == 2 and squats[0] != squats[1]


def test_generation_is_deterministic(library):
    a = generate(library, 5, Goal.GAIN, Experience.INTERMEDIATE)
    b = generate(library, 5, Goal.GAIN, Experience.INTERMEDIATE)
    assert a == b


def test_weekly_volume_is_balanced_between_push_and_pull(library):
    plan = generate(library, 4, Goal.GAIN, Experience.ADVANCED)
    patterns = Counter(p.exercise.pattern for d in plan.days for p in d.exercises)
    push = patterns[Pattern.HORIZONTAL_PUSH] + patterns[Pattern.VERTICAL_PUSH]
    pull = patterns[Pattern.HORIZONTAL_PULL] + patterns[Pattern.VERTICAL_PULL]
    assert push == pull
