from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import consented_user
from app.auth.models import User
from app.common.db import get_db
from app.profile import screening, service
from app.profile.schemas import ProfileIn, ProfileOut, ScreeningIn, ScreeningOut

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("")
def read_profile(user: User = Depends(consented_user), db: Session = Depends(get_db)) -> ProfileOut:
    profile = service.get(db, user.id)
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "profile_missing")
    return service.to_out(profile)


@router.put("")
def save_profile(
    data: ProfileIn, user: User = Depends(consented_user), db: Session = Depends(get_db)
) -> ProfileOut:
    try:
        profile = service.save(db, user.id, data)
    except service.ProfileRuleError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, exc.code) from None
    return service.to_out(profile)


@router.post("/screening")
def submit_screening(
    answers: ScreeningIn, user: User = Depends(consented_user), db: Session = Depends(get_db)
) -> ScreeningOut:
    profile = service.get(db, user.id)
    if profile is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "profile_missing")
    outcome = screening.evaluate(screening.ScreeningAnswers(**answers.model_dump()))
    service.record_screening(db, profile, outcome)
    return ScreeningOut(status=outcome)
