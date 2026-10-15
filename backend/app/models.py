"""Imports every module's models so Alembic and tests see the full schema."""

from app.auth.models import Consent, User, UserSession
from app.logs.models import MealLog, SetLog, WeightLog, WorkoutSession, WorkoutSwap
from app.nutrition.models import Food, NutritionTarget
from app.plans.models import Exercise, Plan, PlanDay, PlanExercise
from app.profile.models import Profile

__all__ = [
    "Consent",
    "Exercise",
    "Food",
    "MealLog",
    "NutritionTarget",
    "Plan",
    "PlanDay",
    "PlanExercise",
    "Profile",
    "SetLog",
    "User",
    "UserSession",
    "WeightLog",
    "WorkoutSession",
    "WorkoutSwap",
]
