from decimal import Decimal
from typing import Any

from app.nutrition.food_sources.open_food_facts import parse_hit

NUTRIMENTS: dict[str, Any] = {
    "energy-kcal_100g": 372,
    "proteins_100g": 13.5,
    "carbohydrates_100g": 58.7,
    "fat_100g": 7,
}
HIT: dict[str, Any] = {
    "code": "5941235004164",
    "product_name": "Fulgi de ovaz",
    "brands": ["Jasmine"],
    "nutriments": NUTRIMENTS,
}


def test_parses_a_complete_hit():
    food = parse_hit(HIT)
    assert food is not None
    assert food.name == "Fulgi de ovaz (Jasmine)"
    assert food.external_id == "5941235004164" and food.source == "open_food_facts"
    assert (food.kcal_100g, food.protein_100g, food.carbs_100g, food.fat_100g) == (
        Decimal("372.0"),
        Decimal("13.5"),
        Decimal("58.7"),
        Decimal("7.0"),
    )


def test_prefers_romanian_name_and_accepts_brand_string():
    food = parse_hit({**HIT, "product_name_ro": "Fulgi de ovăz", "brands": "Jasmine"})
    assert food is not None and food.name == "Fulgi de ovăz (Jasmine)"


def test_skips_incomplete_or_implausible_hits():
    no_fat = {**HIT, "nutriments": {k: v for k, v in NUTRIMENTS.items() if k != "fat_100g"}}
    assert parse_hit(no_fat) is None
    assert parse_hit({**HIT, "code": ""}) is None
    assert parse_hit({**HIT, "product_name": ""}) is None
    too_much = {**HIT, "nutriments": {**NUTRIMENTS, "carbohydrates_100g": 95}}
    assert parse_hit(too_much) is None
    negative = {**HIT, "nutriments": {**NUTRIMENTS, "proteins_100g": -1}}
    assert parse_hit(negative) is None
    garbage = {**HIT, "nutriments": {**NUTRIMENTS, "energy-kcal_100g": "n/a"}}
    assert parse_hit(garbage) is None
