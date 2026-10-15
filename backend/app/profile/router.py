from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import consented_user
from app.auth.models import User
from app.common.db import get_db
from app.profile import screening, service
from app.profile.models import Sex
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
    if profile.sex is Sex.FEMALE and answers.pregnant_or_breastfeeding is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "pregnancy_answer_required")
    outcome = screening.evaluate(
        screening.ScreeningAnswers(
            # The pregnancy question is not shown for male sex; any value sent is ignored.
            pregnant_or_breastfeeding=profile.sex is Sex.FEMALE
            and bool(answers.pregnant_or_breastfeeding),
            diagnosed_medical_condition=answers.diagnosed_medical_condition,
            eating_disorder_history=answers.eating_disorder_history,
            current_injury=answers.current_injury,
        )
    )
    service.record_screening(db, profile, outcome)
    return ScreeningOut(status=outcome)
