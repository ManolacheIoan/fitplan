from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.common.db import get_db
from app.common.errors import DomainError
from app.common.pagination import Limit, Offset, Page, page_of
from app.logs import service as logs_service
from app.plans import service
from app.plans.schemas import (
    ExerciseOut,
    PlanExerciseOut,
    PlanExerciseSwapIn,
    PlanOut,
    PlanSummaryOut,
)
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


@router.get("/exercises/{plan_exercise_id}/alternatives")
def exercise_alternatives(
    plan_exercise_id: int, profile: Profile = Depends(ready_profile), db: Session = Depends(get_db)
) -> list[ExerciseOut]:
    """Exercises that can replace this one (same movement pattern, suitable level)."""
    try:
        planned, plan = service.own_active_plan_exercise(db, profile.user_id, plan_exercise_id)
    except DomainError as e:
        raise HTTPException(e.status, e.code) from None
    return [ExerciseOut.model_validate(e) for e in service.alternatives(db, planned, plan)]


@router.patch("/exercises/{plan_exercise_id}")
def swap_exercise_permanently(
    plan_exercise_id: int,
    data: PlanExerciseSwapIn,
    profile: Profile = Depends(ready_profile),
    db: Session = Depends(get_db),
) -> PlanExerciseOut:
    try:
        planned = service.swap_permanently(
            db,
            profile.user_id,
            plan_exercise_id,
            data.exercise_id,
            logs_service.has_sets_in_open_session(db, profile.user_id, plan_exercise_id),
        )
    except DomainError as e:
        raise HTTPException(e.status, e.code) from None
    return PlanExerciseOut.model_validate(planned)
