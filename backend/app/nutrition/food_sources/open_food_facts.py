"""Open Food Facts adapter (search-a-licious API). Data licence: ODbL; see LICENSING.md.

Their API allows about 10 searches per minute per IP and asks for an identifying
User-Agent, so the nutrition service only calls this on an explicit user action,
rate-limits the calls and caches results in the local `foods` table.
"""

import json
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation
from typing import Any

from app.nutrition.food_sources.base import ExternalFood, FoodSourceError

SEARCH_URL = "https://search.openfoodfacts.org/search"
TIMEOUT_SECONDS = 8
NAME_MAX_LENGTH = 120
_NUTRIENTS = ("energy-kcal_100g", "proteins_100g", "carbohydrates_100g", "fat_100g")


def _decimal(value: Any) -> Decimal | None:
    try:
        number = Decimal(str(value)).quantize(Decimal("0.1"))
    except (InvalidOperation, ValueError):
        return None
    return number if number.is_finite() else None


def parse_hit(hit: dict[str, Any]) -> ExternalFood | None:
    """Normalize one search hit; None when data is missing or implausible.

    Crowd-sourced values can be wrong, so anything outside the ranges the `foods` table
    accepts is skipped rather than stored.
    """
    code = str(hit.get("code") or "").strip()
    name = (hit.get("product_name_ro") or hit.get("product_name") or "").strip()
    nutriments = hit.get("nutriments") or {}
    values = [_decimal(nutriments.get(key)) for key in _NUTRIENTS]
    if not code or not name or any(v is None for v in values):
        return None
    kcal, protein, carbs, fat = (v for v in values if v is not None)
    if not 0 <= kcal <= 900 or min(protein, carbs, fat) < 0 or protein + carbs + fat > 100:
        return None
    brands = hit.get("brands") or []
    if isinstance(brands, str):
        brands = [brands]
    if brands:
        name = f"{name} ({brands[0].strip()})"
    return ExternalFood(
        source=OpenFoodFactsSource.name,
        external_id=code[:64],
        name=name[:NAME_MAX_LENGTH],
        kcal_100g=kcal,
        protein_100g=protein,
        carbs_100g=carbs,
        fat_100g=fat,
    )


class OpenFoodFactsSource:
    name = "open_food_facts"

    def __init__(self, user_agent: str) -> None:
        self.user_agent = user_agent

    def search(self, query: str, limit: int) -> list[ExternalFood]:
        params = urllib.parse.urlencode(
            {
                "q": query,
                "langs": "ro,en",
                "page_size": limit * 2,  # some hits are dropped by validation
                "fields": "code,product_name,product_name_ro,brands,nutriments",
            }
        )
        # The URL is a fixed https constant (only the query string varies).
        request = urllib.request.Request(  # noqa: S310
            f"{SEARCH_URL}?{params}", headers={"User-Agent": self.user_agent}
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
                payload = json.load(response)
        except (OSError, ValueError) as exc:  # network errors, timeouts, invalid JSON
            raise FoodSourceError from exc
        foods = [food for hit in payload.get("hits", []) if (food := parse_hit(hit))]
        return foods[:limit]
