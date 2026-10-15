from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import consented_user
from app.auth.models import User
from app.common.db import get_db
from app.profile import service
from app.profile.models import Profile, ScreeningStatus


def ready_profile(user: User = Depends(consented_user), db: Session = Depends(get_db)) -> Profile:
    """Gate for every feature that needs a completed profile and a passed screening.

    After a screening that recommends professional advice, the app is information-only.
    """
    profile = service.get(db, user.id)
    if profile is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "profile_missing")
    if profile.screening_status is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "screening_required")
    if profile.screening_status is ScreeningStatus.REFER:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "professional_advice_recommended")
    return profile
