"""Adapters for external food databases (see LICENSING.md before enabling one)."""

from app.nutrition.food_sources.base import ExternalFood, FoodSource
from app.nutrition.food_sources.mock import MockFoodSource

__all__ = ["ExternalFood", "FoodSource", "MockFoodSource", "get_food_source"]


def get_food_source(name: str) -> FoodSource | None:
    """Return the configured adapter (FOOD_SOURCE env var); "none" disables lookups."""
    if name == "mock":
        return MockFoodSource()
    return None
