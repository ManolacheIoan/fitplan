"""Plan persistence: generation from the profile, history and lookups."""

from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.plans import generator
from app.plans.models import Exercise, Plan, PlanDay, PlanExercise
from app.plans.schemas import PlanOut
from app.profile.models import Profile, ScreeningStatus

# One query per level (plans -> days -> exercises); exercises join their library row.
_FULL = selectinload(Plan.days).selectinload(PlanDay.exercises)
DAY_EXERCISES = selectinload(PlanDay.exercises)


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


def _inputs_changed(plan: Plan, profile: Profile) -> bool:
    return (plan.days_per_week, plan.goal, plan.experience, plan.equipment) != (
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
    generated = generator.generate(library, profile.training_days, profile.goal, profile.experience)
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
