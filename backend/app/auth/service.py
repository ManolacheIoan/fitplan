"""Accounts, password hashing, sessions and consent."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.models import Consent, User, UserSession
from app.config import get_settings
from app.logs import service as logs_service
from app.nutrition import service as nutrition_service
from app.plans import service as plans_service
from app.profile import service as profile_service

# Bump when the privacy policy changes materially; users must then consent again.
# Keep in sync with the version shown on the frontend privacy page.
PRIVACY_POLICY_VERSION = "2026-10-v4"

_hasher = PasswordHasher()  # argon2id with the library's current recommended parameters
# Guest accounts are temporary: deleted on logout or once their session expires.
GUEST_TTL_DAYS = 7

# Verifying against a dummy hash for unknown emails keeps login timing uniform.
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(16))


class EmailTakenError(Exception):
    pass


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    if password_hash is None:  # guests have no password
        return False
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def register(db: Session, email: str, password: str) -> User:
    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise EmailTakenError from exc
    db.add(Consent(user_id=user.id, policy_version=PRIVACY_POLICY_VERSION))
    db.commit()
    return user


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        verify_password(_DUMMY_HASH, password)
        return None
    return user if verify_password(user.password_hash, password) else None


def session_ttl_days(user: User) -> int:
    return GUEST_TTL_DAYS if user.is_guest else get_settings().session_ttl_days


def create_guest(db: Session) -> User:
    """Temporary account without credentials; consent is recorded like for a registration."""
    purge_expired_guests(db)
    user = User(is_guest=True)
    db.add(user)
    db.flush()
    db.add(Consent(user_id=user.id, policy_version=PRIVACY_POLICY_VERSION))
    db.commit()
    return user


def purge_expired_guests(db: Session) -> int:
    """Hard-delete guests without a valid session (their data goes with them).

    Runs on login, registration and guest start, and daily via the protected maintenance
    endpoint called by a scheduled GitHub Actions workflow. Returns the number deleted.
    """
    active = select(UserSession.id).where(
        UserSession.user_id == User.id, UserSession.expires_at > datetime.now(UTC)
    )
    result = db.execute(delete(User).where(User.is_guest, ~active.exists()))
    db.commit()
    return result.rowcount


def create_session(db: Session, user: User) -> str:
    """Create a session and return the raw token (only its hash is persisted)."""
    token = secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    # Housekeeping without a scheduler: drop this user's expired sessions.
    db.execute(
        delete(UserSession).where(UserSession.user_id == user.id, UserSession.expires_at <= now)
    )
    expires_at = now + timedelta(days=session_ttl_days(user))
    db.add(UserSession(user_id=user.id, token_hash=_hash_token(token), expires_at=expires_at))
    db.commit()
    return token


def user_for_token(db: Session, token: str) -> User | None:
    return db.scalar(
        select(User)
        .join(UserSession, UserSession.user_id == User.id)
        .where(UserSession.token_hash == _hash_token(token))
        .where(UserSession.expires_at > datetime.now(UTC))
    )


def end_session(db: Session, token: str) -> None:
    db.execute(delete(UserSession).where(UserSession.token_hash == _hash_token(token)))
    db.commit()


def change_password(db: Session, user: User, new_password: str) -> None:
    """Change the password and invalidate every session of the user."""
    user.password_hash = hash_password(new_password)
    db.execute(delete(UserSession).where(UserSession.user_id == user.id))
    db.commit()


def has_current_consent(db: Session, user: User) -> bool:
    return (
        db.scalar(
            select(Consent.id).where(
                Consent.user_id == user.id, Consent.policy_version == PRIVACY_POLICY_VERSION
            )
        )
        is not None
    )


def record_consent(db: Session, user: User) -> None:
    if not has_current_consent(db, user):
        db.add(Consent(user_id=user.id, policy_version=PRIVACY_POLICY_VERSION))
        db.commit()


def delete_account(db: Session, user: User) -> None:
    """Hard delete. Every user-owned row (sessions included) is removed by ON DELETE CASCADE."""
    db.delete(user)
    db.commit()


def export_account(db: Session, user: User) -> dict[str, Any]:
    """Everything stored about the user, as JSON-serializable data."""
    consents = db.scalars(select(Consent).where(Consent.user_id == user.id).order_by(Consent.id))
    return {
        "email": user.email,
        "is_guest": user.is_guest,
        "created_at": user.created_at.isoformat(),
        "consents": [
            {"policy_version": c.policy_version, "accepted_at": c.accepted_at.isoformat()}
            for c in consents
        ],
        "profile": profile_service.export(db, user.id),
        "nutrition_targets": nutrition_service.export_targets(db, user.id),
        "own_foods": nutrition_service.export_own_foods(db, user.id),
        "plans": plans_service.export(db, user.id),
        **logs_service.export(db, user.id),
    }
