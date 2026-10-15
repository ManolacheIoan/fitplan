from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.common.db import Base
from app.common.health_constants import WEIGHT_KG_RANGE


class WorkoutSession(Base):
    __tablename__ = "workout_sessions"
    __table_args__ = (
        Index("ix_workout_sessions_user_id_started_at", "user_id", "started_at"),
        # At most one unfinished session per user.
        Index(
            "uq_workout_sessions_one_open_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("finished_at IS NULL"),
        ),
        CheckConstraint(
            "finished_at IS NULL OR finished_at >= started_at", name="finish_after_start"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    plan_day_id: Mapped[int] = mapped_column(
        ForeignKey("plan_days.id", ondelete="CASCADE"), index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SetLog(Base):
    __tablename__ = "set_logs"
    __table_args__ = (
        Index("ix_set_logs_session_id", "session_id"),
        Index("ix_set_logs_exercise_id", "exercise_id"),
        CheckConstraint("weight_kg BETWEEN 0 AND 500", name="weight_range"),
        # Repetitions, or seconds held for timed exercises.
        CheckConstraint("reps BETWEEN 1 AND 300", name="reps_range"),
        CheckConstraint("set_number BETWEEN 1 AND 20", name="set_number_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("workout_sessions.id", ondelete="CASCADE"))
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"))
    set_number: Mapped[int]
    # External load; 0 for bodyweight exercises.
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    reps: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MealLog(Base):
    __tablename__ = "meal_logs"
    __table_args__ = (
        Index("ix_meal_logs_user_id_eaten_on", "user_id", "eaten_on"),
        Index("ix_meal_logs_food_id", "food_id"),
        CheckConstraint("grams > 0 AND grams <= 5000", name="grams_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    food_id: Mapped[int] = mapped_column(ForeignKey("foods.id", ondelete="CASCADE"))
    eaten_on: Mapped[date] = mapped_column(Date)
    grams: Mapped[Decimal] = mapped_column(Numeric(6, 1))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WeightLog(Base):
    __tablename__ = "weight_logs"
    __table_args__ = (
        # Also serves as the (user_id, logged_on) index for range queries.
        UniqueConstraint("user_id", "logged_on"),
        CheckConstraint(
            f"weight_kg BETWEEN {WEIGHT_KG_RANGE[0]} AND {WEIGHT_KG_RANGE[1]}", name="weight_range"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    logged_on: Mapped[date] = mapped_column(Date)
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(4, 1))
