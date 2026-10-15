from datetime import UTC, date, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.common.db import get_db
from app.common.errors import DomainError
from app.common.pagination import Limit, Offset, Page, page_of
from app.logs import service
from app.logs.schemas import (
    DayMealsOut,
    LogDate,
    MealIn,
    MealOut,
    MealUpdate,
    PersonalRecordOut,
    RecentFoodOut,
    SetIn,
    SetLoggedOut,
    SetOut,
    SetUpdate,
    SwapIn,
    TodayOut,
    VolumeProgressOut,
    WeightIn,
    WeightOut,
    WeightProgressOut,
    WeightSavedOut,
    WorkoutOut,
    WorkoutStartIn,
    WorkoutSummaryOut,
)
from app.plans.schemas import PlanDayOut
from app.profile.dependencies import ready_profile
from app.profile.models import Profile

router = APIRouter(tags=["logs"])

Ready = Annotated[Profile, Depends(ready_profile)]
Db = Annotated[Session, Depends(get_db)]
Weeks = Annotated[int, Query(ge=1, le=104)]


def _http(error: DomainError) -> HTTPException:
    return HTTPException(error.status, error.code)


# --- Workouts --------------------------------------------------------------------------------


@router.get("/workouts/today")
def today(profile: Ready, db: Db) -> TodayOut:
    try:
        day, open_id = service.next_day(db, profile.user_id)
    except DomainError as e:
        raise _http(e) from None
    return TodayOut(open_session_id=open_id, next_day=PlanDayOut.model_validate(day))


@router.post("/workouts", status_code=status.HTTP_201_CREATED)
def start_workout(data: WorkoutStartIn, profile: Ready, db: Db) -> WorkoutOut:
    try:
        session = service.start_session(db, profile.user_id, data.plan_day_id)
        return service.workout_detail(db, profile.user_id, session.id)
    except DomainError as e:
        raise _http(e) from None


@router.get("/workouts")
def list_workouts(
    profile: Ready, db: Db, limit: Limit = 20, offset: Offset = 0
) -> Page[WorkoutSummaryOut]:
    items, next_offset = page_of(
        service.workout_history(db, profile.user_id, limit, offset), limit, offset
    )
    return Page(items=items, next_offset=next_offset)


@router.get("/workouts/{workout_id}")
def read_workout(workout_id: int, profile: Ready, db: Db) -> WorkoutOut:
    try:
        return service.workout_detail(db, profile.user_id, workout_id)
    except DomainError as e:
        raise _http(e) from None


@router.post("/workouts/{workout_id}/finish", status_code=status.HTTP_204_NO_CONTENT)
def finish_workout(workout_id: int, profile: Ready, db: Db) -> None:
    try:
        service.finish_session(db, profile.user_id, workout_id)
    except DomainError as e:
        raise _http(e) from None


@router.post("/workouts/{workout_id}/swaps")
def swap_exercise_today(workout_id: int, data: SwapIn, profile: Ready, db: Db) -> WorkoutOut:
    try:
        service.swap_for_session(
            db, profile.user_id, workout_id, data.plan_exercise_id, data.exercise_id
        )
        return service.workout_detail(db, profile.user_id, workout_id)
    except DomainError as e:
        raise _http(e) from None


@router.post("/workouts/{workout_id}/sets", status_code=status.HTTP_201_CREATED)
def add_set(workout_id: int, data: SetIn, profile: Ready, db: Db) -> SetLoggedOut:
    try:
        set_log, is_record = service.add_set(
            db, profile.user_id, workout_id, data.exercise_id, data.weight_kg, data.reps
        )
    except DomainError as e:
        raise _http(e) from None
    return SetLoggedOut(**SetOut.model_validate(set_log).model_dump(), is_record=is_record)


@router.patch("/sets/{set_id}")
def update_set(set_id: int, data: SetUpdate, profile: Ready, db: Db) -> SetOut:
    try:
        set_log = service.update_set(db, profile.user_id, set_id, data.weight_kg, data.reps)
    except DomainError as e:
        raise _http(e) from None
    return SetOut.model_validate(set_log)


@router.delete("/sets/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_set(set_id: int, profile: Ready, db: Db) -> None:
    try:
        service.delete_set(db, profile.user_id, set_id)
    except DomainError as e:
        raise _http(e) from None


# --- Meals -----------------------------------------------------------------------------------


@router.get("/meals")
def meals_for_day(
    day: Annotated[LogDate, Query(alias="date")], profile: Ready, db: Db
) -> DayMealsOut:
    return service.meals_for_day(db, profile.user_id, day)


@router.get("/meals/recent")
def recent_foods(
    profile: Ready, db: Db, limit: Annotated[int, Query(ge=1, le=20)] = 8
) -> list[RecentFoodOut]:
    return service.recent_foods(db, profile.user_id, limit)


@router.post("/meals", status_code=status.HTTP_201_CREATED)
def add_meal(data: MealIn, profile: Ready, db: Db) -> MealOut:
    try:
        return service.add_meal(
            db, profile.user_id, data.food_id, data.eaten_on, data.grams, data.meal_type
        )
    except DomainError as e:
        raise _http(e) from None


@router.patch("/meals/{meal_id}")
def update_meal(meal_id: int, data: MealUpdate, profile: Ready, db: Db) -> MealOut:
    try:
        return service.update_meal(db, profile.user_id, meal_id, data.grams, data.meal_type)
    except DomainError as e:
        raise _http(e) from None


@router.delete("/meals/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal(meal_id: int, profile: Ready, db: Db) -> None:
    try:
        service.delete_meal(db, profile.user_id, meal_id)
    except DomainError as e:
        raise _http(e) from None


# --- Weight and progress -------------------------------------------------------------------


@router.post("/weights")
def save_weight(data: WeightIn, profile: Ready, db: Db) -> WeightSavedOut:
    entry, updated = service.save_weight(db, profile, data.logged_on, data.weight_kg)
    return WeightSavedOut(entry=WeightOut.model_validate(entry), targets_updated=updated)


@router.delete("/weights/{weight_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_weight(weight_id: int, profile: Ready, db: Db) -> None:
    try:
        service.delete_weight(db, profile, weight_id)
    except DomainError as e:
        raise _http(e) from None


def _since(weeks: int) -> date:
    return datetime.now(UTC).date() - timedelta(weeks=weeks)


@router.get("/progress/weight")
def weight_progress(profile: Ready, db: Db, weeks: Weeks = 12) -> WeightProgressOut:
    return service.weight_progress(db, profile.user_id, _since(weeks))


@router.get("/progress/records")
def personal_records(profile: Ready, db: Db) -> list[PersonalRecordOut]:
    return service.personal_records(db, profile.user_id)


@router.get("/progress/volume")
def volume_progress(profile: Ready, db: Db, weeks: Weeks = 12) -> VolumeProgressOut:
    return service.volume_progress(db, profile.user_id, _since(weeks))
