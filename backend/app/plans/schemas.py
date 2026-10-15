from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.plans.models import Pattern, Template
from app.profile.models import Experience, Goal


class ExerciseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    description: str
    pattern: Pattern
    primary_muscle: str
    secondary_muscles: list[str]
    equipment: str
    difficulty: Experience
    is_compound: bool


class PlanExerciseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    sets: int
    reps_min: int
    reps_max: int
    rest_seconds: int
    exercise: ExerciseOut


class PlanDayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    name: str
    exercises: list[PlanExerciseOut]


class PlanSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    template: Template
    days_per_week: int
    goal: Goal
    experience: Experience
    is_active: bool
    created_at: datetime


class PlanOut(PlanSummaryOut):
    days: list[PlanDayOut]
