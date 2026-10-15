from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.common.db import get_db
from app.common.pagination import Limit, Offset, Page, page_of
from app.plans import service
from app.plans.schemas import PlanOut, PlanSummaryOut
from app.profile.dependencies import ready_profile
from app.profile.models import Profile

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("/current")
def current_plan(
    profile: Profile = Depends(ready_profile), db: Session = Depends(get_db)
) -> PlanOut:
    plan = service.active(db, profile.user_id)
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "plan_missing")
    return PlanOut.model_validate(plan)


@router.get("")
def plan_history(
    limit: Limit = 20,
    offset: Offset = 0,
    profile: Profile = Depends(ready_profile),
    db: Session = Depends(get_db),
) -> Page[PlanSummaryOut]:
    items, next_offset = page_of(service.history(db, profile.user_id, limit, offset), limit, offset)
    return Page(items=[PlanSummaryOut.model_validate(p) for p in items], next_offset=next_offset)


@router.get("/{plan_id}")
def read_plan(
    plan_id: int, profile: Profile = Depends(ready_profile), db: Session = Depends(get_db)
) -> PlanOut:
    plan = service.get(db, profile.user_id, plan_id)
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "plan_missing")
    return PlanOut.model_validate(plan)
