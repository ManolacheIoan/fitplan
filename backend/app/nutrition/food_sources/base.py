from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class ExternalFood:
    """A food from an external database, normalized to values per 100 g."""

    source: str  # e.g. "usda_fdc" or "open_food_facts"
    external_id: str
    name: str
    kcal_100g: Decimal
    protein_100g: Decimal
    carbs_100g: Decimal
    fat_100g: Decimal


class FoodSourceError(Exception):
    """The external database could not be reached or returned unusable data."""


class FoodSource(Protocol):
    """Interface every external food database adapter implements.

    Results are cached in the local `foods` table by the nutrition service, so each
    external item is fetched once. Implementations must respect the provider's
    licence, attribution and rate limits (see LICENSING.md).
    """

    name: str

    def search(self, query: str, limit: int) -> list[ExternalFood]: ...
