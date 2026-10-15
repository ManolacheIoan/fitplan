from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.common.db import Base, str_enum


class NutritionTarget(Base):
    """Current daily targets of a user (one row per user, replaced on recompute)."""

    __tablename__ = "nutrition_targets"
    __table_args__ = (
        CheckConstraint(
            "bmr_kcal > 0 AND tdee_kcal > 0 AND kcal > 0 "
            "AND protein_g >= 0 AND fat_g >= 0 AND carbs_g >= 0",
            name="positive_values",
        ),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    bmr_kcal: Mapped[int]
    tdee_kcal: Mapped[int]
    kcal: Mapped[int]
    protein_g: Mapped[int]
    fat_g: Mapped[int]
    carbs_g: Mapped[int]
    weekly_change_kg: Mapped[Decimal] = mapped_column(Numeric(4, 2))
    floor_applied: Mapped[bool]
    # Body weight the targets were computed from (profile weight or 7-day average).
    based_on_weight_kg: Mapped[Decimal] = mapped_column(Numeric(4, 1))
    rules_version: Mapped[int]
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class FoodSourceKind(StrEnum):
    SEED = "seed"  # demo foods shipped with the app
    MANUAL = "manual"  # entered by a user (private to that user)
    EXTERNAL = "external"  # cached from an external food database


class Food(Base):
    """Nutrition values per 100 g. Global rows have no owner; manual rows are private."""

    __tablename__ = "foods"
    __table_args__ = (
        CheckConstraint("kcal_100g BETWEEN 0 AND 900", name="kcal_range"),
        CheckConstraint(
            "protein_100g >= 0 AND carbs_100g >= 0 AND fat_100g >= 0 "
            "AND protein_100g + carbs_100g + fat_100g <= 100",
            name="macros_range",
        ),
        UniqueConstraint("external_source", "external_id"),
        Index("ix_foods_owner_user_id", "owner_user_id"),
        # Trigram index for fast substring search (ILIKE '%term%').
        Index(
            "ix_foods_search_name_trgm",
            "search_name",
            postgresql_using="gin",
            postgresql_ops={"search_name": "gin_trgm_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    # Lower-case, without diacritics: "Măr" is found by "mar".
    search_name: Mapped[str] = mapped_column(String(120))
    kcal_100g: Mapped[Decimal] = mapped_column(Numeric(5, 1))
    protein_100g: Mapped[Decimal] = mapped_column(Numeric(4, 1))
    carbs_100g: Mapped[Decimal] = mapped_column(Numeric(4, 1))
    fat_100g: Mapped[Decimal] = mapped_column(Numeric(4, 1))
    source: Mapped[FoodSourceKind] = mapped_column(str_enum(FoodSourceKind))
    external_source: Mapped[str | None] = mapped_column(String(32))
    external_id: Mapped[str | None] = mapped_column(String(64))
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
