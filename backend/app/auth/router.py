import hmac
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
    GuestIn,
    MeOut,
    PasswordChangeIn,
    RegisterIn,
)
from app.common.client_ip import client_ip
from app.common.db import get_db
from app.common.rate_limit import RateLimiter
from app.common.security import CSRF_COOKIE, SESSION_COOKIE, csrf_token_for
from app.config import get_settings

router = APIRouter(tags=["auth"])

_settings = get_settings()
# Keyed by (email, IP): a stranger guessing passwords cannot lock the owner out of their account.
login_limiter = RateLimiter(_settings.login_rate_limit, _settings.login_rate_window_seconds)
# Keyed by IP alone: caps password spraying across many emails.
login_ip_limiter = RateLimiter(_settings.login_ip_rate_limit, _settings.login_rate_window_seconds)
register_limiter = RateLimiter(_settings.login_rate_limit, _settings.login_rate_window_seconds)


def _set_session_cookies(response: Response, token: str, ttl_days: int) -> None:
    settings = get_settings()
    max_age = ttl_days * 24 * 3600
    common = {"max_age": max_age, "secure": settings.cookie_secure, "samesite": "lax", "path": "/"}
    response.set_cookie(SESSION_COOKIE, token, httponly=True, **common)  # type: ignore[arg-type]
    # Readable by the frontend so it can echo it in the X-CSRF-Token header.
    response.set_cookie(CSRF_COOKIE, csrf_token_for(token), httponly=False, **common)  # type: ignore[arg-type]


def _clear_session_cookies(response: Response) -> None:
    for name in (SESSION_COOKIE, CSRF_COOKIE):
        response.delete_cookie(name, path="/", secure=get_settings().cookie_secure, samesite="lax")


def _start_session(db: Session, response: Response, user: User) -> None:
    token = service.create_session(db, user)
    _set_session_cookies(response, token, service.session_ttl_days(user))


def _me(db: Session, user: User) -> MeOut:
    return MeOut(
        email=user.email,
        is_guest=user.is_guest,
        created_at=user.created_at,
        consent_required=not service.has_current_consent(db, user),
        policy_version=service.PRIVACY_POLICY_VERSION,
    )


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(
    data: RegisterIn, request: Request, response: Response, db: Session = Depends(get_db)
) -> MeOut:
    if not register_limiter.hit(client_ip(request)):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "too_many_attempts")
    try:
        user = service.register(db, data.email, data.password)
    except service.EmailTakenError:
        raise HTTPException(status.HTTP_409_CONFLICT, "email_taken") from None
    service.purge_expired_guests(db)
    _start_session(db, response, user)
    return _me(db, user)


@router.post("/auth/guest", status_code=status.HTTP_201_CREATED)
def continue_as_guest(
    _: GuestIn, request: Request, response: Response, db: Session = Depends(get_db)
) -> MeOut:
    if not register_limiter.hit(client_ip(request)):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "too_many_attempts")
    user = service.create_guest(db)
    _start_session(db, response, user)
    return _me(db, user)


@router.post("/auth/login")
def login(
    data: Credentials, request: Request, response: Response, db: Session = Depends(get_db)
) -> MeOut:
    # Limit per IP and per (email, IP), so neither spraying nor targeted guessing scales,
    # while attempts from elsewhere never block the account owner.
    ip = client_ip(request)
    allowed_ip = login_ip_limiter.hit(ip)
    allowed_pair = login_limiter.hit(f"{data.email}|{ip}")
    if not (allowed_ip and allowed_pair):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "too_many_attempts")
    user = service.authenticate(db, data.email, data.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid_credentials")
    # No scheduler on the free tier: expired guest accounts are removed opportunistically.
    service.purge_expired_guests(db)
    _start_session(db, response, user)
    return _me(db, user)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> None:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        user = service.user_for_token(db, token)
        if user is not None and user.is_guest:
            service.delete_account(db, user)  # a guest's data does not outlive the session
        else:
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
    _start_session(db, response, user)


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
    if not user.is_guest and not service.verify_password(user.password_hash, data.password or ""):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "invalid_credentials")
    service.delete_account(db, user)
    _clear_session_cookies(response)


# --- Internal maintenance (called by a scheduled job, not by browsers) --------------------


@router.post("/internal/purge-guests", include_in_schema=False)
def purge_guests(request: Request, db: Session = Depends(get_db)) -> dict[str, int]:
    token = get_settings().maintenance_token
    if not token:
        raise HTTPException(status.HTTP_404_NOT_FOUND)  # disabled: behave as if absent
    sent = request.headers.get("authorization", "").removeprefix("Bearer ")
    if not hmac.compare_digest(sent.encode(), token.encode()):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid_token")
    return {"deleted": service.purge_expired_guests(db)}
