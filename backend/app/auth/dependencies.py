"""Request dependencies used by every protected router."""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth import service
from app.auth.models import User
from app.common.db import get_db
from app.common.security import SESSION_COOKIE


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(SESSION_COOKIE)
    user = service.user_for_token(db, token) if token else None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not_authenticated")
    return user


def consented_user(user: User = Depends(current_user), db: Session = Depends(get_db)) -> User:
    """The app is unusable without consent for the current privacy policy version."""
    if not service.has_current_consent(db, user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "consent_required")
    return user
