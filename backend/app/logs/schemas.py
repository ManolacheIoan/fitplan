from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from app.common.health_constants import WEIGHT_KG_RANGE
from app.nutrition.schemas import FoodOut, TargetsOut
from app.plans.schemas import PlanDayOut, PlanExerciseOut


def _sane_log_date(value: date) -> date:
    # Users log in their local date; allow one day ahead of UTC for time zones.
    if not date(2000, 1, 1) <= value <= datetime.now(UTC).date() + timedelta(days=1):
        raise ValueError("date out of range")
    return value


LogDate = Annotated[date, AfterValidator(_sane_log_date)]
LoadKg = Annotated[Decimal, Field(ge=0, le=500, decimal_places=2)]
# Repetitions, or seconds held for timed exercises.
Reps = Annotated[int, Field(ge=1, le=300)]
BodyWeightKg = Annotated[
    Decimal, Field(ge=WEIGHT_KG_RANGE[0], le=WEIGHT_KG_RANGE[1], decimal_places=1)
]
Grams = Annotated[Decimal, Field(gt=0, le=5000, decimal_places=1)]


# --- Workouts --------------------------------------------------------------------------------


class WorkoutStartIn(BaseModel):
    plan_day_id: int


class SetIn(BaseModel):
    exercise_id: int
    weight_kg: LoadKg
    reps: Reps


class SwapIn(BaseModel):
    plan_exercise_id: int
    exercise_id: int


class SetUpdate(BaseModel):
    weight_kg: LoadKg | None = None
    reps: Reps | None = None


class SetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exercise_id: int
    set_number: int
    weight_kg: Decimal
    reps: int


class LastSetOut(BaseModel):
    weight_kg: Decimal
    reps: int


class SuggestionOut(BaseModel):
    kind: Literal["first_time", "add_weight", "add_reps", "max_reached"]
    weight_kg: Decimal | None


class WorkoutExerciseOut(BaseModel):
    planned: PlanExerciseOut
    # True when the exercise was replaced for this session only.
    swapped_today: bool
    sets: list[SetOut]
    last_sets: list[LastSetOut]
    suggestion: SuggestionOut


class WorkoutDayOut(BaseModel):
    id: int
    position: int
    name: str


class WorkoutOut(BaseModel):
    id: int
    day: WorkoutDayOut
    started_at: datetime
    finished_at: datetime | None
    exercises: list[WorkoutExerciseOut]


class WorkoutSummaryOut(BaseModel):
    id: int
    day_name: str
    started_at: datetime
    finished_at: datetime | None
    sets_count: int
    volume_kg: Decimal


class TodayOut(BaseModel):
    open_session_id: int | None
    next_day: PlanDayOut


# --- Meals -----------------------------------------------------------------------------------


class MealIn(BaseModel):
    food_id: int
    eaten_on: LogDate
    grams: Grams


class MealUpdate(BaseModel):
    grams: Grams


class Macros(BaseModel):
    kcal: Decimal
    protein_g: Decimal
    carbs_g: Decimal
    fat_g: Decimal


class MealOut(Macros):
    id: int
    food: FoodOut
    eaten_on: date
    grams: Decimal


class DayMealsOut(BaseModel):
    date: date
    entries: list[MealOut]
    totals: Macros
    targets: TargetsOut | None


# --- Weight and progress -------------------------------------------------------------------


class WeightIn(BaseModel):
    logged_on: LogDate
    weight_kg: BodyWeightKg


class WeightOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    logged_on: date
    weight_kg: Decimal


class WeightSavedOut(BaseModel):
    entry: WeightOut
    # True when the targets were recomputed from the weekly average ("Țintele au fost actualizate").
    targets_updated: bool


class WeeklyWeight(BaseModel):
    week_start: date
    average_kg: Decimal


class WeightProgressOut(BaseModel):
    entries: list[WeightOut]
    weekly: list[WeeklyWeight]


class WeeklyVolume(BaseModel):
    week_start: date
    volume_kg: Decimal
    sessions: int


class VolumeProgressOut(BaseModel):
    weekly: list[WeeklyVolume]
