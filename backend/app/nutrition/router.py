from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.common.db import get_db
from app.common.errors import DomainError
from app.nutrition import service
from app.nutrition.schemas import FoodIn, FoodOut, TargetsOut, TargetsResponse
from app.profile.dependencies import ready_profile
from app.profile.models import Profile

router = APIRouter(tags=["nutrition"])


@router.get("/nutrition/targets")
def read_targets(
    profile: Profile = Depends(ready_profile), db: Session = Depends(get_db)
) -> TargetsResponse:
    target = service.current(db, profile.user_id)
    if target is None:
        # With a passed screening, targets are only ever withheld by the BMI rule.
        return TargetsResponse(status="blocked", reason=service.BLOCKED_BMI)
    return TargetsResponse(status="ok", targets=TargetsOut.model_validate(target))


@router.get("/foods")
def search_foods(
    q: Annotated[str, Query(min_length=2, max_length=60)],
    limit: Annotated[int, Query(ge=1, le=30)] = 15,
    profile: Profile = Depends(ready_profile),
    db: Session = Depends(get_db),
) -> list[FoodOut]:
    foods = service.search_foods(db, profile.user_id, q, limit)
    return [service.to_out(f, profile.user_id) for f in foods]


@router.get("/foods/external")
def search_external_foods(
    q: Annotated[str, Query(min_length=3, max_length=60)],
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
    profile: Profile = Depends(ready_profile),
    db: Session = Depends(get_db),
) -> list[FoodOut]:
    """Explicit search in the external food database (not as-you-type)."""
    try:
        foods = service.search_external(db, profile.user_id, q, limit)
    except DomainError as e:
        raise HTTPException(e.status, e.code) from None
    return [service.to_out(f, profile.user_id) for f in foods]


@router.post("/foods", status_code=status.HTTP_201_CREATED)
def create_food(
    data: FoodIn, profile: Profile = Depends(ready_profile), db: Session = Depends(get_db)
) -> FoodOut:
    return service.to_out(service.create_manual_food(db, profile.user_id, data), profile.user_id)
