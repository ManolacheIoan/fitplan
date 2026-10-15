from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.db import Base, str_enum
from app.profile.models import Equipment, Experience, Goal


class Pattern(StrEnum):
    SQUAT = "squat"
    HINGE = "hinge"
    LUNGE = "lunge"
    HORIZONTAL_PUSH = "horizontal_push"
    VERTICAL_PUSH = "vertical_push"
    HORIZONTAL_PULL = "horizontal_pull"
    VERTICAL_PULL = "vertical_pull"
    CHEST_ISOLATION = "chest_isolation"
    SHOULDER_ISOLATION = "shoulder_isolation"
    BICEPS = "biceps"
    TRICEPS = "triceps"
    QUAD_ISOLATION = "quad_isolation"
    HAMSTRING_ISOLATION = "hamstring_isolation"
    GLUTE_ISOLATION = "glute_isolation"
    CALVES = "calves"
    CORE = "core"


class RepScheme(StrEnum):
    """How an exercise is prescribed; values live in plans/constants.py PRESCRIPTION."""

    STRENGTH = "strength"  # heavy barbell lifts: fewer reps, longer rest
    COMPOUND = "compound"  # machine / dumbbell multi-joint
    ISOLATION = "isolation"  # single-joint
    BODYWEIGHT_HARD = "bodyweight_hard"  # pull-ups, dips, nordics: low rep counts
    CALVES = "calves"
    CORE = "core"
    TIMED = "timed"  # held for time (plank): "reps" are seconds


class Template(StrEnum):
    FULL_BODY = "full_body"
    UPPER_LOWER = "upper_lower"
    PUSH_PULL_LEGS = "push_pull_legs"
    BRO_SPLIT = "bro_split"


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    pattern: Mapped[Pattern] = mapped_column(str_enum(Pattern))
    rep_scheme: Mapped[RepScheme] = mapped_column(str_enum(RepScheme))
    primary_muscle: Mapped[str] = mapped_column(String(16))
    secondary_muscles: Mapped[list[str]] = mapped_column(ARRAY(String(16)))
    # Equipment type of the exercise itself (all are available in a regular gym).
    equipment: Mapped[str] = mapped_column(String(16))
    difficulty: Mapped[Experience] = mapped_column(str_enum(Experience))
    is_compound: Mapped[bool]


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = (
        Index("ix_plans_user_id_created_at", "user_id", "created_at"),
        # At most one active plan per user.
        Index(
            "uq_plans_one_active_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("is_active"),
        ),
        CheckConstraint("days_per_week BETWEEN 2 AND 6", name="days_per_week_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    template: Mapped[Template] = mapped_column(str_enum(Template))
    # Snapshot of the profile inputs used to generate the plan.
    days_per_week: Mapped[int]
    goal: Mapped[Goal] = mapped_column(str_enum(Goal))
    experience: Mapped[Experience] = mapped_column(str_enum(Experience))
    equipment: Mapped[Equipment] = mapped_column(str_enum(Equipment))
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    days: Mapped[list["PlanDay"]] = relationship(
        order_by="PlanDay.position", cascade="all, delete-orphan", passive_deletes=True
    )


class PlanDay(Base):
    __tablename__ = "plan_days"
    __table_args__ = (UniqueConstraint("plan_id", "position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="CASCADE"))
    position: Mapped[int]
    name: Mapped[str] = mapped_column(String(50))

    exercises: Mapped[list["PlanExercise"]] = relationship(
        order_by="PlanExercise.position", cascade="all, delete-orphan", passive_deletes=True
    )


class PlanExercise(Base):
    __tablename__ = "plan_exercises"
    __table_args__ = (
        UniqueConstraint("plan_day_id", "position"),
        CheckConstraint("sets BETWEEN 1 AND 10", name="sets_range"),
        # Seconds for timed exercises, hence the upper bound above typical rep counts.
        CheckConstraint("reps_min >= 1 AND reps_min <= reps_max AND reps_max <= 120", name="reps"),
        CheckConstraint("rest_seconds BETWEEN 30 AND 300", name="rest_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_day_id: Mapped[int] = mapped_column(ForeignKey("plan_days.id", ondelete="CASCADE"))
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"), index=True)
    position: Mapped[int]
    sets: Mapped[int]
    reps_min: Mapped[int]
    reps_max: Mapped[int]
    rest_seconds: Mapped[int]

    exercise: Mapped[Exercise] = relationship(lazy="joined")
