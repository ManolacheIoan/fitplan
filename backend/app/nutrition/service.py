"""Stores the user's current nutrition targets, always re-running the safety rules."""

import unicodedata
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.config import get_settings
from app.nutrition import rules
from app.nutrition.food_sources import get_food_source
from app.nutrition.models import Food, FoodSourceKind, NutritionTarget
from app.nutrition.schemas import FoodIn, FoodOut, TargetsOut
from app.profile import screening
from app.profile.models import Profile, ScreeningStatus

BLOCKED_BMI = "weight_loss_blocked_bmi"


def blocked_reason(profile: Profile, weight_kg: Decimal) -> str | None:
    if not screening.goal_allowed(profile.goal, weight_kg, profile.height_cm):
        return BLOCKED_BMI
    return None


def recompute(db: Session, profile: Profile, weight_kg: Decimal | None = None) -> None:
    """Recompute targets from `weight_kg` (default: profile weight).

    Targets are removed instead when screening did not pass or a safety rule blocks them.
    Does not commit.
    """
    weight = weight_kg if weight_kg is not None else profile.weight_kg
    db.execute(delete(NutritionTarget).where(NutritionTarget.user_id == profile.user_id))
    db.flush()
    if profile.screening_status is not ScreeningStatus.PASSED or blocked_reason(profile, weight):
        return
    age = screening.age_on(profile.birth_date, datetime.now(UTC).date())
    result = rules.compute_targets(
        rules.NutritionInput(
            sex=profile.sex,
            age_years=age,
            height_cm=float(profile.height_cm),
            weight_kg=float(weight),
            activity_level=profile.activity_level,
            goal=profile.goal,
        )
    )
    db.add(
        NutritionTarget(
            user_id=profile.user_id,
            bmr_kcal=result.bmr_kcal,
            tdee_kcal=result.tdee_kcal,
            kcal=result.kcal,
            protein_g=result.protein_g,
            fat_g=result.fat_g,
            carbs_g=result.carbs_g,
            weekly_change_kg=Decimal(str(result.weekly_change_kg)),
            floor_applied=result.floor_applied,
            based_on_weight_kg=weight,
            rules_version=rules.RULES_VERSION,
        )
    )


def current(db: Session, user_id: int) -> NutritionTarget | None:
    return db.get(NutritionTarget, user_id)


def export_targets(db: Session, user_id: int) -> dict[str, Any] | None:
    target = current(db, user_id)
    return TargetsOut.model_validate(target).model_dump(mode="json") if target else None


# --- Foods ---------------------------------------------------------------------------------


def normalize(text: str) -> str:
    """Lower-case and strip diacritics (ă, â, î, ș, ț) for accent-insensitive search."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).strip()


def _visible_to(user_id: int) -> Any:
    return or_(Food.owner_user_id.is_(None), Food.owner_user_id == user_id)


def to_out(food: Food, user_id: int) -> FoodOut:
    out = FoodOut.model_validate(food)
    out.is_own = food.owner_user_id == user_id
    return out


def _search_local(db: Session, user_id: int, term: str, limit: int) -> list[Food]:
    return list(
        db.scalars(
            select(Food)
            .where(_visible_to(user_id), Food.search_name.contains(term, autoescape=True))
            .order_by(
                Food.search_name.startswith(term, autoescape=True).desc(),
                func.length(Food.name),
                Food.name,
            )
            .limit(limit)
        )
    )


def _cache_external(db: Session, term: str, limit: int) -> None:
    source = get_food_source(get_settings().food_source)
    if source is None:
        return
    items = source.search(term, limit)
    if not items:
        return
    stmt = insert(Food).values(
        [
            {
                "name": item.name,
                "search_name": normalize(item.name),
                "kcal_100g": item.kcal_100g,
                "protein_100g": item.protein_100g,
                "carbs_100g": item.carbs_100g,
                "fat_100g": item.fat_100g,
                "source": FoodSourceKind.EXTERNAL,
                "external_source": item.source,
                "external_id": item.external_id,
            }
            for item in items
        ]
    )
    db.execute(stmt.on_conflict_do_nothing(index_elements=["external_source", "external_id"]))
    db.commit()


def search_foods(db: Session, user_id: int, query: str, limit: int) -> list[Food]:
    """Local search first; the external source is asked only when results are few.

    External results are cached in `foods`, so later searches stay local.
    """
    term = normalize(query)
    found = _search_local(db, user_id, term, limit)
    if len(found) < limit:
        _cache_external(db, term, limit - len(found))
        found = _search_local(db, user_id, term, limit)
    return found


def create_manual_food(db: Session, user_id: int, data: FoodIn) -> Food:
    food = Food(
        **data.model_dump(),
        search_name=normalize(data.name),
        source=FoodSourceKind.MANUAL,
        owner_user_id=user_id,
    )
    db.add(food)
    db.commit()
    return food


def accessible_food(db: Session, user_id: int, food_id: int) -> Food | None:
    return db.scalar(select(Food).where(Food.id == food_id, _visible_to(user_id)))


def export_own_foods(db: Session, user_id: int) -> list[dict[str, Any]]:
    foods = db.scalars(select(Food).where(Food.owner_user_id == user_id).order_by(Food.id))
    return [to_out(f, user_id).model_dump(mode="json") for f in foods]
