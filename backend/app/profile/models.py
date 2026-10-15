from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.common.db import Base, str_enum
from app.common.health_constants import HEIGHT_CM_RANGE, WEIGHT_KG_RANGE


class Sex(StrEnum):
    MALE = "male"
    FEMALE = "female"


class ActivityLevel(StrEnum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"


class Goal(StrEnum):
    LOSE = "lose"
    MAINTAIN = "maintain"
    GAIN = "gain"


class Experience(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Equipment(StrEnum):
    GYM = "gym"


class Program(StrEnum):
    """Split chosen by the user; AUTO lets the generator pick one for the days per week."""

    AUTO = "auto"
    FULL_BODY = "full_body"
    UPPER_LOWER = "upper_lower"
    PUSH_PULL_LEGS = "push_pull_legs"
    BRO_SPLIT = "bro_split"


class ScreeningStatus(StrEnum):
    PASSED = "passed"
    # At least one "yes": nothing is generated; the user is referred to a professional.
    REFER = "refer"


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (
        CheckConstraint(
            f"height_cm BETWEEN {HEIGHT_CM_RANGE[0]} AND {HEIGHT_CM_RANGE[1]}", name="height_range"
        ),
        CheckConstraint(
            f"weight_kg BETWEEN {WEIGHT_KG_RANGE[0]} AND {WEIGHT_KG_RANGE[1]}", name="weight_range"
        ),
        CheckConstraint("training_days BETWEEN 2 AND 6", name="training_days_range"),
        CheckConstraint("length(display_name) BETWEEN 1 AND 50", name="display_name_length"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    display_name: Mapped[str] = mapped_column(String(50))
    sex: Mapped[Sex] = mapped_column(str_enum(Sex))
    birth_date: Mapped[date] = mapped_column(Date)
    height_cm: Mapped[Decimal] = mapped_column(Numeric(4, 1))
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(4, 1))
    activity_level: Mapped[ActivityLevel] = mapped_column(str_enum(ActivityLevel))
    goal: Mapped[Goal] = mapped_column(str_enum(Goal))
    training_days: Mapped[int]
    experience: Mapped[Experience] = mapped_column(str_enum(Experience))
    equipment: Mapped[Equipment] = mapped_column(str_enum(Equipment))
    program: Mapped[Program] = mapped_column(str_enum(Program), server_default=Program.AUTO.value)
    # Only the outcome of the safety screening is stored, never the individual answers.
    screening_status: Mapped[ScreeningStatus | None] = mapped_column(str_enum(ScreeningStatus))
    screening_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
