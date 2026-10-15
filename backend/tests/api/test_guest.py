from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.auth.models import User, UserSession
from app.auth.service import GUEST_TTL_DAYS
from app.common.security import SESSION_COOKIE
from app.config import Settings, get_settings
from tests.conftest import PASSWORD, with_csrf
from tests.factories import API, onboard


def guest(app) -> TestClient:
    c = TestClient(app, base_url="https://testserver")
    r = c.post(f"{API}/auth/guest", json={"consent": True})
    assert r.status_code == 201, r.text
    assert r.json()["is_guest"] is True and r.json()["email"] is None
    return with_csrf(c)


def test_guest_requires_consent(client):
    assert client.post(f"{API}/auth/guest", json={"consent": False}).status_code == 422
    assert client.post(f"{API}/auth/guest", json={}).status_code == 422


def test_guest_can_use_the_app(app):
    c = guest(app)
    onboard(c)
    assert c.get(f"{API}/plans/current").status_code == 200
    assert c.get(f"{API}/account/export").json()["is_guest"] is True


def test_guest_session_lasts_seven_days(app, db: Session):
    guest(app)
    expires = db.scalar(select(UserSession.expires_at))
    assert expires is not None
    assert (
        timedelta(days=GUEST_TTL_DAYS - 1)
        < expires - datetime.now(UTC)
        <= timedelta(days=GUEST_TTL_DAYS)
    )


def test_guest_logout_deletes_all_data(app, db: Session):
    c = guest(app)
    onboard(c)
    assert c.post(f"{API}/auth/logout").status_code == 204
    assert db.scalar(select(func.count()).select_from(User).where(User.is_guest)) == 0


def test_expired_guests_are_purged(app, db: Session, make_user):
    guest(app)
    db.execute(update(UserSession).values(expires_at=datetime.now(UTC) - timedelta(minutes=1)))
    make_user()  # any registration/login/guest start runs the purge
    assert db.scalar(select(func.count()).select_from(User).where(User.is_guest)) == 0


def test_guest_cannot_change_password_and_deletes_without_one(app, db: Session):
    c = guest(app)
    r = c.post(
        f"{API}/auth/password",
        json={"current_password": "x", "new_password": PASSWORD},
    )
    assert r.status_code == 403
    assert c.request("DELETE", f"{API}/account", json={}).status_code == 204
    assert db.scalar(select(func.count()).select_from(User)) == 0


def test_registered_user_logout_keeps_data(make_user, db: Session):
    c = make_user()
    c.post(f"{API}/auth/logout")
    assert db.scalar(select(func.count()).select_from(User)) == 1
    assert SESSION_COOKIE not in c.cookies


def test_guests_are_isolated_from_each_other(app):
    a, b = guest(app), guest(app)
    onboard(a)
    onboard(b)
    plan_id = a.get(f"{API}/plans/current").json()["id"]
    assert b.get(f"{API}/plans/{plan_id}").status_code == 404


# --- Scheduled cleanup endpoint ---------------------------------------------------------------

TOKEN = "t" * 40
PURGE = f"{API}/internal/purge-guests"


def test_purge_endpoint_disabled_without_token(client):
    assert client.post(PURGE, headers={"Authorization": f"Bearer {TOKEN}"}).status_code == 404


def test_purge_endpoint_rejects_wrong_token(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "maintenance_token", TOKEN)
    assert client.post(PURGE).status_code == 401
    assert client.post(PURGE, headers={"Authorization": "Bearer nope"}).status_code == 401


def test_purge_endpoint_deletes_only_expired_guests(
    app, client, db: Session, make_user, monkeypatch
):
    monkeypatch.setattr(get_settings(), "maintenance_token", TOKEN)
    expired, active = guest(app), guest(app)
    onboard(expired)
    make_user("regular@example.com")
    # The first guest created is the one whose session we expire.
    expired_id = db.scalar(select(User.id).where(User.is_guest).order_by(User.id).limit(1))
    db.execute(
        update(UserSession)
        .where(UserSession.user_id == expired_id)
        .values(expires_at=datetime.now(UTC) - timedelta(minutes=1))
    )

    r = client.post(PURGE, headers={"Authorization": f"Bearer {TOKEN}"})
    assert r.status_code == 200 and r.json() == {"deleted": 1}
    assert db.get(User, expired_id) is None
    assert active.get(f"{API}/auth/me").status_code == 200
    assert db.scalar(select(func.count()).select_from(User).where(~User.is_guest)) == 1
    # Running it again is harmless.
    assert client.post(PURGE, headers={"Authorization": f"Bearer {TOKEN}"}).json() == {"deleted": 0}


def test_short_maintenance_token_is_rejected():
    with pytest.raises(ValidationError):
        Settings(database_url="postgresql://x", secret_key="s", maintenance_token="short")
