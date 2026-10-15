"""In-memory adapter used in development and tests (FOOD_SOURCE=mock). No network."""

from decimal import Decimal

from app.nutrition.food_sources.base import ExternalFood

_ITEMS = [
    ExternalFood(
        "mock", "1", "Hummus (exemplu extern)", Decimal(166), Decimal(8), Decimal(14), Decimal(10)
    ),
    ExternalFood(
        "mock",
        "2",
        "Quinoa fiartă (exemplu extern)",
        Decimal(120),
        Decimal("4.4"),
        Decimal("21.3"),
        Decimal("1.9"),
    ),
]


class MockFoodSource:
    name = "mock"

    def search(self, query: str, limit: int) -> list[ExternalFood]:
        term = query.lower()
        return [item for item in _ITEMS if term in item.name.lower()][:limit]
