from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.nutrition.models import FoodSourceKind


class TargetsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bmr_kcal: int
    tdee_kcal: int
    kcal: int
    protein_g: int
    fat_g: int
    carbs_g: int
    weekly_change_kg: Decimal
    floor_applied: bool
    based_on_weight_kg: Decimal
    computed_at: datetime


class TargetsResponse(BaseModel):
    status: Literal["ok", "blocked"]
    # Set when blocked, e.g. "weight_loss_blocked_bmi".
    reason: str | None = None
    targets: TargetsOut | None = None


class FoodIn(BaseModel):
    """Manual food entry; values per 100 g."""

    name: str = Field(min_length=2, max_length=120)
    kcal_100g: Decimal = Field(ge=0, le=900, decimal_places=1)
    protein_100g: Decimal = Field(ge=0, le=100, decimal_places=1)
    carbs_100g: Decimal = Field(ge=0, le=100, decimal_places=1)
    fat_100g: Decimal = Field(ge=0, le=100, decimal_places=1)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if len(value) < 2:
            raise ValueError("name too short")
        return value

    @model_validator(mode="after")
    def macros_fit_in_100g(self) -> "FoodIn":
        if self.protein_100g + self.carbs_100g + self.fat_100g > 100:
            raise ValueError("protein + carbs + fat cannot exceed 100 g per 100 g")
        return self


class FoodOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    kcal_100g: Decimal
    protein_100g: Decimal
    carbs_100g: Decimal
    fat_100g: Decimal
    source: FoodSourceKind
    is_own: bool = False
    # Required credit for data from an external database (e.g. Open Food Facts, ODbL).
    attribution: str | None = None
