"""Seed reference data: `python -m seed` (idempotent, safe to re-run)."""

from sqlalchemy import Engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.common.db import get_engine
from app.nutrition.models import Food, FoodSourceKind
from app.nutrition.service import normalize
from app.plans.models import Exercise
from seed.exercises import EXERCISES
from seed.foods import DEMO_FOODS

FIELDS = (
    "slug",
    "name",
    "pattern",
    "rep_scheme",
    "primary_muscle",
    "secondary_muscles",
    "equipment",
    "difficulty",
    "is_compound",
    "description",
)


def seed_exercises(session: Session) -> int:
    rows = [dict(zip(FIELDS, exercise, strict=True)) for exercise in EXERCISES]
    stmt = insert(Exercise).values(rows)
    # Upsert by slug: existing plans keep their exercise ids, texts get updated.
    stmt = stmt.on_conflict_do_update(
        index_elements=[Exercise.slug],
        set_={k: stmt.excluded[k] for k in rows[0] if k != "slug"},
    )
    session.execute(stmt)
    return len(rows)


def seed_foods(session: Session) -> int:
    rows = [
        {
            "name": name,
            "search_name": normalize(name),
            "kcal_100g": kcal,
            "protein_100g": protein,
            "carbs_100g": carbs,
            "fat_100g": fat,
            "source": FoodSourceKind.SEED,
            "external_source": "seed",
            "external_id": slug,
        }
        for slug, name, kcal, protein, carbs, fat in DEMO_FOODS
    ]
    stmt = insert(Food).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Food.external_source, Food.external_id],
        set_={k: stmt.excluded[k] for k in rows[0] if k not in {"external_source", "external_id"}},
    )
    session.execute(stmt)
    return len(rows)


def run(engine: Engine) -> None:
    with Session(engine) as session:
        exercises = seed_exercises(session)
        foods = seed_foods(session)
        session.commit()
    print(f"Seeded {exercises} exercises and {foods} demo foods.")


if __name__ == "__main__":
    run(get_engine())
