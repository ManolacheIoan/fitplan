from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator

from app.common.health_constants import HEIGHT_CM_RANGE, WEIGHT_KG_RANGE
from app.profile.models import ActivityLevel, Equipment, Experience, Goal, ScreeningStatus, Sex

Height = Field(ge=HEIGHT_CM_RANGE[0], le=HEIGHT_CM_RANGE[1], decimal_places=1)
Weight = Field(ge=WEIGHT_KG_RANGE[0], le=WEIGHT_KG_RANGE[1], decimal_places=1)


class ProfileIn(BaseModel):
    display_name: str = Field(min_length=1, max_length=50)
    sex: Sex
    birth_date: date
    height_cm: Decimal = Height
    weight_kg: Decimal = Weight
    activity_level: ActivityLevel
    goal: Goal
    training_days: int = Field(ge=2, le=6)
    experience: Experience
    equipment: Equipment = Equipment.GYM

    @field_validator("display_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("display_name must not be blank")
        return value


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    display_name: str
    sex: Sex
    birth_date: date
    age: int
    height_cm: Decimal
    weight_kg: Decimal
    activity_level: ActivityLevel
    goal: Goal
    training_days: int
    experience: Experience
    equipment: Equipment
    screening_status: ScreeningStatus | None
    screening_at: datetime | None


class ScreeningIn(BaseModel):
    """Answers are evaluated in memory and discarded; only the outcome is stored."""

    # Asked only when the biological sex is female; required in that case (see router).
    pregnant_or_breastfeeding: StrictBool | None = None
    diagnosed_medical_condition: StrictBool
    eating_disorder_history: StrictBool
    current_injury: StrictBool


class ScreeningOut(BaseModel):
    status: ScreeningStatus
