"""Plan persistence: generation from the profile, history and lookups."""

from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.common.errors import DomainError
from app.plans import generator
from app.plans.models import Exercise, Plan, PlanDay, PlanExercise, RepScheme, Template
from app.plans.schemas import PlanOut
from app.profile.models import Profile, ScreeningStatus

# One query per level (plans -> days -> exercises); exercises join their library row.
_FULL = selectinload(Plan.days).selectinload(PlanDay.exercises)
DAY_EXERCISES = selectinload(PlanDay.exercises)


def is_loadable(exercise: Exercise) -> bool:
    """Whether adding external weight is the natural progression for the exercise."""
    if exercise.rep_scheme is RepScheme.TIMED:
        return False
    return exercise.equipment != "bodyweight" or exercise.rep_scheme is RepScheme.STRENGTH


def own_active_plan_exercise(
    db: Session, user_id: int, plan_exercise_id: int
) -> tuple[PlanExercise, Plan]:
    """A plan exercise of the user's active plan (other users' rows look missing)."""
    row = db.execute(
        select(PlanExercise, Plan)
        .join(PlanDay, PlanDay.id == PlanExercise.plan_day_id)
        .join(Plan, Plan.id == PlanDay.plan_id)
        .where(PlanExercise.id == plan_exercise_id, Plan.user_id == user_id, Plan.is_active)
    ).first()
    if row is None:
        raise DomainError("plan_exercise_not_found", 404)
    return row[0], row[1]


def alternatives(db: Session, planned: PlanExercise, plan: Plan) -> list[Exercise]:
    """Same movement pattern, allowed for the plan's level, not already in that day."""
    in_day = select(PlanExercise.exercise_id).where(PlanExercise.plan_day_id == planned.plan_day_id)
    pattern = planned.exercise.pattern
    pool = db.scalars(
        select(Exercise).where(Exercise.pattern == pattern, Exercise.id.not_in(in_day))
    )
    return generator.candidates_by_pattern(list(pool), plan.experience).get(pattern, [])


def check_alternative(db: Session, planned: PlanExercise, plan: Plan, exercise_id: int) -> Exercise:
    for exercise in alternatives(db, planned, plan):
        if exercise.id == exercise_id:
            return exercise
    raise DomainError("exercise_not_allowed", 422)


def swap_permanently(
    db: Session, user_id: int, plan_exercise_id: int, exercise_id: int, logged_in_open_session: bool
) -> PlanExercise:
    """Replace the exercise in the active plan; sets/reps/rest follow the new exercise."""
    planned, plan = own_active_plan_exercise(db, user_id, plan_exercise_id)
    if logged_in_open_session:
        raise DomainError("sets_already_logged", 409)
    exercise = check_alternative(db, planned, plan, exercise_id)
    p = generator.prescription(exercise, plan.goal, plan.experience)
    planned.exercise_id = exercise.id
    planned.sets, planned.reps_min, planned.reps_max = p.sets, p.reps_min, p.reps_max
    planned.rest_seconds = p.rest_seconds
    db.commit()
    db.refresh(planned)
    return planned


def active(db: Session, user_id: int) -> Plan | None:
    return db.scalar(select(Plan).options(_FULL).where(Plan.user_id == user_id, Plan.is_active))


def get(db: Session, user_id: int, plan_id: int) -> Plan | None:
    # Filtering by user_id makes other users' plans indistinguishable from missing ones.
    return db.scalar(select(Plan).options(_FULL).where(Plan.id == plan_id, Plan.user_id == user_id))


def history(db: Session, user_id: int, limit: int, offset: int) -> list[Plan]:
    return list(
        db.scalars(
            select(Plan)
            .where(Plan.user_id == user_id)
            .order_by(Plan.created_at.desc(), Plan.id.desc())
            .limit(limit + 1)
            .offset(offset)
        )
    )


def _deactivate(db: Session, user_id: int) -> None:
    db.execute(update(Plan).where(Plan.user_id == user_id, Plan.is_active).values(is_active=False))


def _template_for(profile: Profile) -> Template:
    template = generator.resolve_template(profile.program, profile.training_days)
    if template is None:  # prevented by profile validation
        raise ValueError("program does not support this number of days")
    return template


def _inputs_changed(plan: Plan, profile: Profile) -> bool:
    return (plan.template, plan.days_per_week, plan.goal, plan.experience, plan.equipment) != (
        _template_for(profile),
        profile.training_days,
        profile.goal,
        profile.experience,
        profile.equipment,
    )


def sync_with_profile(db: Session, profile: Profile) -> None:
    """Regenerate the active plan when its inputs changed; old plans stay in history.

    Without a passed screening no plan is active. Does not commit.
    """
    current = active(db, profile.user_id)
    if profile.screening_status is not ScreeningStatus.PASSED:
        _deactivate(db, profile.user_id)
        return
    if current is not None and not _inputs_changed(current, profile):
        return
    _deactivate(db, profile.user_id)
    db.flush()
    library = list(db.scalars(select(Exercise)))
    generated = generator.generate(
        library, _template_for(profile), profile.training_days, profile.goal, profile.experience
    )
    db.add(
        Plan(
            user_id=profile.user_id,
            template=generated.template,
            days_per_week=profile.training_days,
            goal=profile.goal,
            experience=profile.experience,
            equipment=profile.equipment,
            days=[
                PlanDay(
                    position=day_index,
                    name=day.name,
                    exercises=[
                        PlanExercise(
                            exercise_id=p.exercise.id,
                            position=index,
                            sets=p.sets,
                            reps_min=p.reps_min,
                            reps_max=p.reps_max,
                            rest_seconds=p.rest_seconds,
                        )
                        for index, p in enumerate(day.exercises, start=1)
                    ],
                )
                for day_index, day in enumerate(generated.days, start=1)
            ],
        )
    )


def export(db: Session, user_id: int) -> list[dict[str, Any]]:
    plans = db.scalars(
        select(Plan).options(_FULL).where(Plan.user_id == user_id).order_by(Plan.created_at)
    )
    return [PlanOut.model_validate(p).model_dump(mode="json") for p in plans]
