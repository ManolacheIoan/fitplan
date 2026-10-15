from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from fastapi import APIRouter, HTTPException, status


@dataclass(frozen=True)
class ParsedMealItem:
    food_name: str
    grams: Decimal


class MealParser(Protocol):
    """V2 contract: turn a free-text meal description into food items with quantities.

    Results must be shown to the user for confirmation before anything is logged.
    """

    def parse(self, text: str) -> list[ParsedMealItem]: ...


router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/meal-parse")
def parse_meal() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "not_implemented")
