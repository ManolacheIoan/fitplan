"""Workout, meal and weight logs plus progress aggregates.

Every query is scoped by user_id; rows of other users behave as if they did not exist.
"""

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import Date, Numeric, cast, delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.common.errors import DomainError
from app.config import get_settings
from app.logs.models import MealLog, MealType, SetLog, WeightLog, WorkoutSession, WorkoutSwap
from app.logs.schemas import (
    DayMealsOut,
    LastSetOut,
    Macros,
    MealOut,
    PersonalRecordOut,
    RecentFoodOut,
    SetOut,
    SuggestionOut,
    VolumeProgressOut,
    WeeklyVolume,
    WeeklyWeight,
    WeightOut,
    WeightProgressOut,
    WorkoutDayOut,
    WorkoutExerciseOut,
    WorkoutOut,
    WorkoutSummaryOut,
)
from app.nutrition import service as nutrition_service
from app.nutrition.models import Food
from app.nutrition.schemas import TargetsOut
from app.plans import generator, progression
from app.plans import service as plans_service
from app.plans.models import Exercise, Plan, PlanDay, PlanExercise
from app.plans.schemas import ExerciseOut, PlanExerciseOut
from app.profile.models import Profile

TARGETS_RECOMPUTE_INTERVAL = timedelta(days=7)
WEEKLY_AVERAGE_DAYS = 7
MAX_SETS_PER_EXERCISE = 20


class LogError(DomainError):
    pass


def _not_found(what: str) -> LogError:
    return LogError(f"{what}_not_found", 404)


# --- Workouts --------------------------------------------------------------------------------


def _open_session(db: Session, user_id: int) -> WorkoutSession | None:
    return db.scalar(
        select(WorkoutSession).where(
            WorkoutSession.user_id == user_id, WorkoutSession.finished_at.is_(None)
        )
    )


def next_day(db: Session, user_id: int) -> tuple[PlanDay, int | None]:
    """Next day of the active plan's rotation, and the unfinished session id if any."""
    plan = plans_service.active(db, user_id)
    if plan is None or not plan.days:
        raise LogError("plan_missing", 404)
    last_position = db.scalar(
        select(PlanDay.position)
        .join(WorkoutSession, WorkoutSession.plan_day_id == PlanDay.id)
        .where(PlanDay.plan_id == plan.id, WorkoutSession.finished_at.is_not(None))
        .order_by(WorkoutSession.started_at.desc())
        .limit(1)
    )
    index = 0 if last_position is None else last_position % len(plan.days)
    open_session = _open_session(db, user_id)
    return plan.days[index], open_session.id if open_session else None


def start_session(db: Session, user_id: int, plan_day_id: int) -> WorkoutSession:
    day_in_active_plan = db.scalar(
        select(PlanDay.id)
        .join(Plan, Plan.id == PlanDay.plan_id)
        .where(PlanDay.id == plan_day_id, Plan.user_id == user_id, Plan.is_active)
    )
    if day_in_active_plan is None:
        raise _not_found("plan_day")
    if _open_session(db, user_id) is not None:
        raise LogError("session_open", 409)
    session = WorkoutSession(user_id=user_id, plan_day_id=plan_day_id)
    db.add(session)
    db.commit()
    return session


def _own_session(db: Session, user_id: int, session_id: int) -> WorkoutSession:
    session = db.scalar(
        select(WorkoutSession).where(
            WorkoutSession.id == session_id, WorkoutSession.user_id == user_id
        )
    )
    if session is None:
        raise _not_found("workout")
    return session


def _last_sets_by_exercise(
    db: Session, user_id: int, exercise_ids: list[int], exclude_session_id: int
) -> dict[int, list[SetLog]]:
    """Sets of the most recent other finished session, per exercise (2 queries total)."""
    latest = (
        select(SetLog.exercise_id, WorkoutSession.id.label("session_id"))
        .join(WorkoutSession, WorkoutSession.id == SetLog.session_id)
        .where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.id != exclude_session_id,
            WorkoutSession.finished_at.is_not(None),
            SetLog.exercise_id.in_(exercise_ids),
        )
        .order_by(SetLog.exercise_id, WorkoutSession.started_at.desc())
        .distinct(SetLog.exercise_id)
        .subquery()
    )
    rows = db.scalars(
        select(SetLog)
        .join(
            latest,
            (latest.c.exercise_id == SetLog.exercise_id)
            & (latest.c.session_id == SetLog.session_id),
        )
        .order_by(SetLog.set_number)
    )
    grouped: dict[int, list[SetLog]] = defaultdict(list)
    for row in rows:
        grouped[row.exercise_id].append(row)
    return grouped


def _effective(planned: PlanExercise, swapped: Exercise | None, plan: Plan) -> PlanExerciseOut:
    """The planned exercise, or today's replacement prescribed for this plan."""
    if swapped is None:
        return PlanExerciseOut.model_validate(planned)
    p = generator.prescription(swapped, plan.goal, plan.experience)
    return PlanExerciseOut(
        id=planned.id,
        position=planned.position,
        sets=p.sets,
        reps_min=p.reps_min,
        reps_max=p.reps_max,
        rest_seconds=p.rest_seconds,
        exercise=ExerciseOut.model_validate(swapped),
    )


def _workout_exercise(
    planned: PlanExerciseOut,
    exercise: Exercise,
    sets: list[SetLog],
    last: list[SetLog],
    swapped_today: bool,
) -> WorkoutExerciseOut:
    suggestion = progression.suggest(
        [progression.LoggedSet(s.weight_kg, s.reps) for s in last],
        planned.reps_max,
        exercise.pattern,
        exercise.is_compound,
        loadable=plans_service.is_loadable(exercise),
    )
    return WorkoutExerciseOut(
        planned=planned,
        swapped_today=swapped_today,
        sets=[SetOut.model_validate(s) for s in sets],
        last_sets=[LastSetOut(weight_kg=s.weight_kg, reps=s.reps) for s in last],
        suggestion=SuggestionOut(kind=suggestion.kind, weight_kg=suggestion.weight_kg),
    )


def _swaps(db: Session, session_id: int) -> dict[int, Exercise]:
    """plan_exercise_id -> replacement exercise, for one session (one query)."""
    rows = db.execute(
        select(WorkoutSwap.plan_exercise_id, Exercise)
        .join(Exercise, Exercise.id == WorkoutSwap.exercise_id)
        .where(WorkoutSwap.session_id == session_id)
    )
    return {plan_exercise_id: exercise for plan_exercise_id, exercise in rows}


def workout_detail(db: Session, user_id: int, session_id: int) -> WorkoutOut:
    session = _own_session(db, user_id, session_id)
    day = db.scalars(
        select(PlanDay)
        .options(plans_service.DAY_EXERCISES)
        .where(PlanDay.id == session.plan_day_id)
    ).one()
    plan = db.scalars(select(Plan).where(Plan.id == day.plan_id)).one()
    swaps = _swaps(db, session.id)
    logged = db.scalars(
        select(SetLog).where(SetLog.session_id == session.id).order_by(SetLog.set_number)
    )
    sets_by_exercise: dict[int, list[SetLog]] = defaultdict(list)
    for s in logged:
        sets_by_exercise[s.exercise_id].append(s)
    effective = [(pe, swaps.get(pe.id, pe.exercise)) for pe in day.exercises]
    last = _last_sets_by_exercise(db, user_id, [ex.id for _, ex in effective], session.id)
    exercises = [
        _workout_exercise(
            _effective(pe, swaps.get(pe.id), plan),
            ex,
            sets_by_exercise[ex.id],
            last.get(ex.id, []),
            swapped_today=pe.id in swaps,
        )
        for pe, ex in effective
    ]
    return WorkoutOut(
        id=session.id,
        day=WorkoutDayOut(id=day.id, position=day.position, name=day.name),
        started_at=session.started_at,
        finished_at=session.finished_at,
        exercises=exercises,
    )


def _allowed_exercise_ids(db: Session, session: WorkoutSession) -> set[int]:
    planned = db.scalars(
        select(PlanExercise.exercise_id).where(PlanExercise.plan_day_id == session.plan_day_id)
    )
    return set(planned) | {e.id for e in _swaps(db, session.id).values()}


def has_sets_in_open_session(db: Session, user_id: int, plan_exercise_id: int) -> bool:
    """Whether the unfinished session already has sets for this plan exercise's exercise."""
    open_session = _open_session(db, user_id)
    if open_session is None:
        return False
    planned = db.get(PlanExercise, plan_exercise_id)
    if planned is None or planned.plan_day_id != open_session.plan_day_id:
        return False
    exercise = _swaps(db, open_session.id).get(planned.id, planned.exercise)
    count = db.scalar(
        select(func.count()).where(
            SetLog.session_id == open_session.id, SetLog.exercise_id == exercise.id
        )
    )
    return bool(count)


def swap_for_session(
    db: Session, user_id: int, session_id: int, plan_exercise_id: int, exercise_id: int
) -> None:
    """Replace an exercise for this session only. Choosing the planned one undoes it."""
    session = _own_session(db, user_id, session_id)
    if session.finished_at is not None:
        raise LogError("workout_finished", 409)
    planned = db.scalar(
        select(PlanExercise).where(
            PlanExercise.id == plan_exercise_id,
            PlanExercise.plan_day_id == session.plan_day_id,
        )
    )
    if planned is None:
        raise _not_found("plan_exercise")
    current = _swaps(db, session.id).get(planned.id, planned.exercise)
    if db.scalar(
        select(func.count()).where(
            SetLog.session_id == session.id, SetLog.exercise_id == current.id
        )
    ):
        raise LogError("sets_already_logged", 409)
    db.execute(
        delete(WorkoutSwap).where(
            WorkoutSwap.session_id == session.id, WorkoutSwap.plan_exercise_id == planned.id
        )
    )
    if exercise_id != planned.exercise_id:
        plan = db.scalars(
            select(Plan)
            .join(PlanDay, PlanDay.plan_id == Plan.id)
            .where(PlanDay.id == planned.plan_day_id)
        ).one()
        plans_service.check_alternative(db, planned, plan, exercise_id)
        db.add(
            WorkoutSwap(session_id=session.id, plan_exercise_id=planned.id, exercise_id=exercise_id)
        )
    db.commit()


def add_set(
    db: Session, user_id: int, session_id: int, exercise_id: int, weight_kg: Decimal, reps: int
) -> tuple[SetLog, bool]:
    """Log a set; also returns whether it is a new personal record (heaviest weight)."""
    session = _own_session(db, user_id, session_id)
    if exercise_id not in _allowed_exercise_ids(db, session):
        raise LogError("exercise_not_in_workout", 422)
    count = db.scalar(
        select(func.count()).where(
            SetLog.session_id == session.id, SetLog.exercise_id == exercise_id
        )
    )
    if (count or 0) >= MAX_SETS_PER_EXERCISE:
        raise LogError("too_many_sets", 422)
    previous_best = _best_weight(db, user_id, exercise_id)
    set_log = SetLog(
        session_id=session.id,
        exercise_id=exercise_id,
        set_number=(count or 0) + 1,
        weight_kg=weight_kg,
        reps=reps,
    )
    db.add(set_log)
    db.commit()
    is_record = previous_best is not None and weight_kg > previous_best
    return set_log, is_record


def _best_weight(db: Session, user_id: int, exercise_id: int) -> Decimal | None:
    """Heaviest external load logged so far for the exercise (None if never logged)."""
    return db.scalar(
        select(func.max(SetLog.weight_kg))
        .join(WorkoutSession, WorkoutSession.id == SetLog.session_id)
        .where(WorkoutSession.user_id == user_id, SetLog.exercise_id == exercise_id)
    )


def personal_records(db: Session, user_id: int) -> list[PersonalRecordOut]:
    """Heaviest set per exercise (ties: more reps, then the earliest). One query."""
    rows = db.execute(
        select(SetLog.exercise_id, Exercise.name, SetLog.weight_kg, SetLog.reps, SetLog.created_at)
        .join(WorkoutSession, WorkoutSession.id == SetLog.session_id)
        .join(Exercise, Exercise.id == SetLog.exercise_id)
        .where(WorkoutSession.user_id == user_id, SetLog.weight_kg > 0)
        .order_by(
            SetLog.exercise_id,
            SetLog.weight_kg.desc(),
            SetLog.reps.desc(),
            SetLog.created_at,
        )
        .distinct(SetLog.exercise_id)
    )
    records = [
        PersonalRecordOut(
            exercise_id=r[0], exercise_name=r[1], weight_kg=r[2], reps=r[3], achieved_on=r[4]
        )
        for r in rows
    ]
    return sorted(records, key=lambda r: r.exercise_name)


def _own_set(db: Session, user_id: int, set_id: int) -> SetLog:
    set_log = db.scalar(
        select(SetLog)
        .join(WorkoutSession, WorkoutSession.id == SetLog.session_id)
        .where(SetLog.id == set_id, WorkoutSession.user_id == user_id)
    )
    if set_log is None:
        raise _not_found("set")
    return set_log


def update_set(
    db: Session, user_id: int, set_id: int, weight_kg: Decimal | None, reps: int | None
) -> SetLog:
    set_log = _own_set(db, user_id, set_id)
    if weight_kg is not None:
        set_log.weight_kg = weight_kg
    if reps is not None:
        set_log.reps = reps
    db.commit()
    return set_log


def delete_set(db: Session, user_id: int, set_id: int) -> None:
    set_log = _own_set(db, user_id, set_id)
    db.delete(set_log)
    db.flush()
    # Keep set numbers contiguous for that exercise.
    remaining = db.scalars(
        select(SetLog)
        .where(SetLog.session_id == set_log.session_id, SetLog.exercise_id == set_log.exercise_id)
        .order_by(SetLog.set_number)
    )
    for number, row in enumerate(remaining, start=1):
        row.set_number = number
    db.commit()


def finish_session(db: Session, user_id: int, session_id: int) -> None:
    session = _own_session(db, user_id, session_id)
    if session.finished_at is None:
        session.finished_at = datetime.now(UTC)
        db.commit()


def workout_history(db: Session, user_id: int, limit: int, offset: int) -> list[WorkoutSummaryOut]:
    # One aggregate query: no per-session lookups.
    rows = db.execute(
        select(
            WorkoutSession.id,
            PlanDay.name,
            WorkoutSession.started_at,
            WorkoutSession.finished_at,
            func.count(SetLog.id),
            func.coalesce(func.sum(SetLog.weight_kg * SetLog.reps), 0),
        )
        .join(PlanDay, PlanDay.id == WorkoutSession.plan_day_id)
        .outerjoin(SetLog, SetLog.session_id == WorkoutSession.id)
        .where(WorkoutSession.user_id == user_id)
        .group_by(WorkoutSession.id, PlanDay.name)
        .order_by(WorkoutSession.started_at.desc())
        .limit(limit + 1)
        .offset(offset)
    )
    return [
        WorkoutSummaryOut(
            id=r[0],
            day_name=r[1],
            started_at=r[2],
            finished_at=r[3],
            sets_count=r[4],
            volume_kg=r[5],
        )
        for r in rows
    ]


# --- Meals -----------------------------------------------------------------------------------


def _scaled(value: Decimal, grams: Decimal) -> Decimal:
    return (value * grams / 100).quantize(Decimal("0.1"))


def _meal_out(meal: MealLog, food: Food, user_id: int) -> MealOut:
    return MealOut(
        id=meal.id,
        food=nutrition_service.to_out(food, user_id),
        eaten_on=meal.eaten_on,
        grams=meal.grams,
        meal_type=meal.meal_type,
        kcal=_scaled(food.kcal_100g, meal.grams),
        protein_g=_scaled(food.protein_100g, meal.grams),
        carbs_g=_scaled(food.carbs_100g, meal.grams),
        fat_g=_scaled(food.fat_100g, meal.grams),
    )


def add_meal(
    db: Session, user_id: int, food_id: int, eaten_on: date, grams: Decimal, meal_type: MealType
) -> MealOut:
    food = nutrition_service.accessible_food(db, user_id, food_id)
    if food is None:
        raise _not_found("food")
    meal = MealLog(
        user_id=user_id, food_id=food.id, eaten_on=eaten_on, grams=grams, meal_type=meal_type
    )
    db.add(meal)
    db.commit()
    return _meal_out(meal, food, user_id)


def _own_meal(db: Session, user_id: int, meal_id: int) -> tuple[MealLog, Food]:
    row = db.execute(
        select(MealLog, Food)
        .join(Food, Food.id == MealLog.food_id)
        .where(MealLog.id == meal_id, MealLog.user_id == user_id)
    ).first()
    if row is None:
        raise _not_found("meal")
    return row[0], row[1]


def update_meal(
    db: Session, user_id: int, meal_id: int, grams: Decimal, meal_type: MealType | None
) -> MealOut:
    meal, food = _own_meal(db, user_id, meal_id)
    meal.grams = grams
    if meal_type is not None:
        meal.meal_type = meal_type
    db.commit()
    return _meal_out(meal, food, user_id)


def delete_meal(db: Session, user_id: int, meal_id: int) -> None:
    meal, _ = _own_meal(db, user_id, meal_id)
    db.delete(meal)
    db.commit()


def recent_foods(db: Session, user_id: int, limit: int) -> list[RecentFoodOut]:
    """Distinct foods the user logged most recently, with the last quantity used."""
    # Ids grow with insertion order, so they order entries even within one transaction.
    latest = (
        select(MealLog.food_id, MealLog.grams, MealLog.id)
        .where(MealLog.user_id == user_id)
        .order_by(MealLog.food_id, MealLog.id.desc())
        .distinct(MealLog.food_id)
        .subquery()
    )
    rows = db.execute(
        select(Food, latest.c.grams)
        .join(latest, latest.c.food_id == Food.id)
        .order_by(latest.c.id.desc())
        .limit(limit)
    )
    return [
        RecentFoodOut(food=nutrition_service.to_out(food, user_id), grams=grams)
        for food, grams in rows
    ]


def meals_for_day(db: Session, user_id: int, day: date) -> DayMealsOut:
    rows = db.execute(
        select(MealLog, Food)
        .join(Food, Food.id == MealLog.food_id)
        .where(MealLog.user_id == user_id, MealLog.eaten_on == day)
        .order_by(MealLog.created_at, MealLog.id)
    ).all()
    entries = [_meal_out(meal, food, user_id) for meal, food in rows]
    target = nutrition_service.current(db, user_id)
    return DayMealsOut(
        date=day,
        entries=entries,
        totals=Macros(
            kcal=sum((e.kcal for e in entries), Decimal(0)),
            protein_g=sum((e.protein_g for e in entries), Decimal(0)),
            carbs_g=sum((e.carbs_g for e in entries), Decimal(0)),
            fat_g=sum((e.fat_g for e in entries), Decimal(0)),
        ),
        targets=TargetsOut.model_validate(target) if target else None,
    )


# --- Weight ----------------------------------------------------------------------------------


def _latest_weight(db: Session, user_id: int) -> WeightLog | None:
    return db.scalar(
        select(WeightLog)
        .where(WeightLog.user_id == user_id)
        .order_by(WeightLog.logged_on.desc())
        .limit(1)
    )


def _weekly_average(db: Session, user_id: int, until: date) -> Decimal:
    since = until - timedelta(days=WEEKLY_AVERAGE_DAYS - 1)
    # Called right after saving an entry inside the window, so AVG is never NULL.
    average = db.execute(
        select(func.avg(WeightLog.weight_kg)).where(
            WeightLog.user_id == user_id, WeightLog.logged_on.between(since, until)
        )
    ).scalar_one()
    return Decimal(average).quantize(Decimal("0.1"))


def save_weight(
    db: Session, profile: Profile, logged_on: date, weight_kg: Decimal
) -> tuple[WeightLog, bool]:
    """Upsert the day's weight, sync the profile weight and, at most once per week,
    recompute targets from the 7-day average. Returns (entry, targets_updated).

    The recompute re-runs every safety rule (BMI threshold, calorie floor).
    """
    values = insert(WeightLog).values(
        user_id=profile.user_id, logged_on=logged_on, weight_kg=weight_kg
    )
    upsert = values.on_conflict_do_update(
        index_elements=["user_id", "logged_on"], set_={"weight_kg": values.excluded.weight_kg}
    ).returning(WeightLog)
    entry = db.scalars(upsert, execution_options={"populate_existing": True}).one()
    # A back-dated entry must not overwrite a more recent weight.
    latest = _latest_weight(db, profile.user_id) or entry
    profile.weight_kg = latest.weight_kg

    targets = nutrition_service.current(db, profile.user_id)
    due = targets is None or targets.computed_at <= datetime.now(UTC) - TARGETS_RECOMPUTE_INTERVAL
    if due:
        average = _weekly_average(db, profile.user_id, latest.logged_on)
        nutrition_service.recompute(db, profile, average)
    db.commit()
    return entry, due


def delete_weight(db: Session, profile: Profile, weight_id: int) -> None:
    deleted = db.execute(
        delete(WeightLog).where(WeightLog.id == weight_id, WeightLog.user_id == profile.user_id)
    )
    if deleted.rowcount == 0:
        raise _not_found("weight")
    latest = _latest_weight(db, profile.user_id)
    if latest is not None:
        profile.weight_kg = latest.weight_kg
    db.commit()


# --- Progress --------------------------------------------------------------------------------


def weight_progress(db: Session, user_id: int, since: date) -> WeightProgressOut:
    entries = db.scalars(
        select(WeightLog)
        .where(WeightLog.user_id == user_id, WeightLog.logged_on >= since)
        .order_by(WeightLog.logged_on)
    ).all()
    week = cast(func.date_trunc("week", WeightLog.logged_on), Date)
    weekly = db.execute(
        select(week, cast(func.avg(WeightLog.weight_kg), Numeric(4, 1)))
        .where(WeightLog.user_id == user_id, WeightLog.logged_on >= since)
        .group_by(week)
        .order_by(week)
    )
    return WeightProgressOut(
        entries=[WeightOut.model_validate(e) for e in entries],
        weekly=[WeeklyWeight(week_start=w, average_kg=avg) for w, avg in weekly],
    )


def volume_progress(db: Session, user_id: int, since: date) -> VolumeProgressOut:
    local_start = func.timezone(get_settings().app_timezone, WorkoutSession.started_at)
    week = cast(func.date_trunc("week", local_start), Date)
    rows = db.execute(
        select(
            week,
            func.coalesce(func.sum(SetLog.weight_kg * SetLog.reps), 0),
            func.count(func.distinct(WorkoutSession.id)),
        )
        .outerjoin(SetLog, SetLog.session_id == WorkoutSession.id)
        .where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.finished_at.is_not(None),
            cast(local_start, Date) >= since,
        )
        .group_by(week)
        .order_by(week)
    )
    return VolumeProgressOut(
        weekly=[WeeklyVolume(week_start=w, volume_kg=v, sessions=n) for w, v, n in rows]
    )


# --- Export ----------------------------------------------------------------------------------


def export(db: Session, user_id: int) -> dict[str, Any]:
    sessions = db.scalars(
        select(WorkoutSession).where(WorkoutSession.user_id == user_id).order_by(WorkoutSession.id)
    ).all()
    sets = db.scalars(
        select(SetLog)
        .join(WorkoutSession, WorkoutSession.id == SetLog.session_id)
        .where(WorkoutSession.user_id == user_id)
        .order_by(SetLog.id)
    ).all()
    meals = db.execute(
        select(MealLog, Food)
        .join(Food, Food.id == MealLog.food_id)
        .where(MealLog.user_id == user_id)
        .order_by(MealLog.eaten_on, MealLog.id)
    ).all()
    weights = db.scalars(
        select(WeightLog).where(WeightLog.user_id == user_id).order_by(WeightLog.logged_on)
    ).all()
    sets_by_session: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for s in sets:
        sets_by_session[s.session_id].append(SetOut.model_validate(s).model_dump(mode="json"))
    return {
        "workouts": [
            {
                "id": w.id,
                "plan_day_id": w.plan_day_id,
                "started_at": w.started_at.isoformat(),
                "finished_at": w.finished_at.isoformat() if w.finished_at else None,
                "sets": sets_by_session[w.id],
                "swaps": [
                    {"plan_exercise_id": pe_id, "exercise_id": ex.id}
                    for pe_id, ex in _swaps(db, w.id).items()
                ],
            }
            for w in sessions
        ],
        "meals": [_meal_out(m, f, user_id).model_dump(mode="json") for m, f in meals],
        "weights": [WeightOut.model_validate(w).model_dump(mode="json") for w in weights],
    }
