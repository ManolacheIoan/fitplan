"""Adapters for external food databases (see LICENSING.md before enabling one)."""

from app.config import get_settings
from app.nutrition.food_sources.base import ExternalFood, FoodSource, FoodSourceError
from app.nutrition.food_sources.mock import MockFoodSource
from app.nutrition.food_sources.open_food_facts import OpenFoodFactsSource

__all__ = [
    "ExternalFood",
    "FoodSource",
    "FoodSourceError",
    "MockFoodSource",
    "OpenFoodFactsSource",
    "get_food_source",
]

ATTRIBUTION = {"open_food_facts": "Open Food Facts (ODbL)", "mock": "Mock"}


def get_food_source(name: str) -> FoodSource | None:
    """Return the configured adapter (FOOD_SOURCE env var); "none" disables lookups."""
    if name == "mock":
        return MockFoodSource()
    if name == "open_food_facts":
        return OpenFoodFactsSource(get_settings().off_user_agent)
    return None
