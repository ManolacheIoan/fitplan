"""Stores the user's current nutrition targets, always re-running the safety rules."""

import time
import unicodedata
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.common.errors import DomainError
from app.common.rate_limit import RateLimiter
from app.config import get_settings
from app.nutrition import rules
from app.nutrition.food_sources import (
    ATTRIBUTION,
    ExternalFood,
    FoodSourceError,
    get_food_source,
)
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
    out.attribution = ATTRIBUTION.get(food.external_source or "")
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


# Open Food Facts allows ~10 searches/min per IP; stay below it for the whole app.
external_limiter = RateLimiter(limit=8, window_seconds=60)
external_user_limiter = RateLimiter(limit=4, window_seconds=60)
SEARCHED_TERM_TTL_SECONDS = 24 * 3600
_searched_terms: dict[tuple[str, str], float] = {}


def _recently_searched(source: str, term: str) -> bool:
    expires = _searched_terms.get((source, term))
    return expires is not None and expires > time.monotonic()


def reset_external_search_state() -> None:
    external_limiter.reset()
    external_user_limiter.reset()
    _searched_terms.clear()


def _cache_external(db: Session, items: list[ExternalFood]) -> None:
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
    """Local search only (fast, as-you-type). External databases are searched on demand."""
    return _search_local(db, user_id, normalize(query), limit)


def search_external(db: Session, user_id: int, query: str, limit: int) -> list[Food]:
    """Search the configured external database on an explicit user action.

    Results are cached in `foods`; the same term is not sent again for 24 h, and calls are
    rate-limited per user and for the whole app.
    """
    source = get_food_source(get_settings().food_source)
    if source is None:
        raise DomainError("food_source_disabled", 404)
    term = normalize(query)
    if not _recently_searched(source.name, term):
        if not external_user_limiter.hit(f"user:{user_id}") or not external_limiter.hit("all"):
            raise DomainError("food_source_busy", 429)
        try:
            items = source.search(term, limit)
        except FoodSourceError:
            raise DomainError("food_source_unavailable", 503) from None
        _cache_external(db, items)
        _searched_terms[(source.name, term)] = time.monotonic() + SEARCHED_TERM_TTL_SECONDS
    return list(
        db.scalars(
            select(Food)
            .where(
                Food.external_source == source.name,
                Food.search_name.contains(term, autoescape=True),
            )
            .order_by(func.length(Food.name), Food.name)
            .limit(limit)
        )
    )


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
