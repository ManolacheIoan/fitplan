from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.auth import service
from app.auth.dependencies import current_user
from app.auth.models import User
from app.auth.schemas import (
    AccountDeleteIn,
    ConsentIn,
    Credentials,
    MeOut,
    PasswordChangeIn,
    RegisterIn,
)
from app.common.db import get_db
from app.common.rate_limit import RateLimiter
from app.common.security import CSRF_COOKIE, SESSION_COOKIE, csrf_token_for
from app.config import get_settings

router = APIRouter(tags=["auth"])

_settings = get_settings()
login_limiter = RateLimiter(_settings.login_rate_limit, _settings.login_rate_window_seconds)
register_limiter = RateLimiter(_settings.login_rate_limit, _settings.login_rate_window_seconds)


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _set_session_cookies(response: Response, token: str) -> None:
    settings = get_settings()
    max_age = settings.session_ttl_days * 24 * 3600
    common = {"max_age": max_age, "secure": settings.cookie_secure, "samesite": "lax", "path": "/"}
    response.set_cookie(SESSION_COOKIE, token, httponly=True, **common)  # type: ignore[arg-type]
    # Readable by the frontend so it can echo it in the X-CSRF-Token header.
    response.set_cookie(CSRF_COOKIE, csrf_token_for(token), httponly=False, **common)  # type: ignore[arg-type]


def _clear_session_cookies(response: Response) -> None:
    for name in (SESSION_COOKIE, CSRF_COOKIE):
        response.delete_cookie(name, path="/", secure=get_settings().cookie_secure, samesite="lax")


def _me(db: Session, user: User) -> MeOut:
    return MeOut(
        email=user.email,
        created_at=user.created_at,
        consent_required=not service.has_current_consent(db, user),
        policy_version=service.PRIVACY_POLICY_VERSION,
    )


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(
    data: RegisterIn, request: Request, response: Response, db: Session = Depends(get_db)
) -> MeOut:
    if not register_limiter.hit(_client_ip(request)):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "too_many_attempts")
    try:
        user = service.register(db, data.email, data.password)
    except service.EmailTakenError:
        raise HTTPException(status.HTTP_409_CONFLICT, "email_taken") from None
    _set_session_cookies(response, service.create_session(db, user))
    return _me(db, user)


@router.post("/auth/login")
def login(
    data: Credentials, request: Request, response: Response, db: Session = Depends(get_db)
) -> MeOut:
    # Limit per IP and per account, so neither spraying nor targeted guessing scales.
    allowed_ip = login_limiter.hit(f"ip:{_client_ip(request)}")
    allowed_email = login_limiter.hit(f"email:{data.email}")
    if not (allowed_ip and allowed_email):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "too_many_attempts")
    user = service.authenticate(db, data.email, data.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid_credentials")
    _set_session_cookies(response, service.create_session(db, user))
    return _me(db, user)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> None:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        service.end_session(db, token)
    _clear_session_cookies(response)


@router.get("/auth/me")
def me(user: User = Depends(current_user), db: Session = Depends(get_db)) -> MeOut:
    return _me(db, user)


@router.post("/auth/consent", status_code=status.HTTP_204_NO_CONTENT)
def give_consent(
    _: ConsentIn, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> None:
    service.record_consent(db, user)


@router.post("/auth/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    data: PasswordChangeIn,
    response: Response,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> None:
    if not service.verify_password(user.password_hash, data.current_password):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "invalid_credentials")
    service.change_password(db, user, data.new_password)
    # All sessions were invalidated; keep the current device signed in with a fresh one.
    _set_session_cookies(response, service.create_session(db, user))


@router.get("/account/export")
def export_data(
    # Not gated on consent: users can always get their data out.
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return service.export_account(db, user)


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    data: AccountDeleteIn,
    response: Response,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> None:
    if not service.verify_password(user.password_hash, data.password):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "invalid_credentials")
    service.delete_account(db, user)
    _clear_session_cookies(response)
