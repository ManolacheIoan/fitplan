from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.auth.models import Consent, User, UserSession
from app.auth.service import PRIVACY_POLICY_VERSION
from app.common.security import CSRF_HEADER, SESSION_COOKIE
from tests.conftest import API, PASSWORD, with_csrf


def register(client: TestClient, email: str = "ana@example.com", **extra: object):
    body = {"email": email, "password": PASSWORD, "consent": True, **extra}
    return client.post(f"{API}/auth/register", json=body)


def test_register_sets_httponly_secure_session_and_records_consent(client, db: Session):
    r = register(client, email="  Ana@Example.com ")
    assert r.status_code == 201
    assert r.json()["email"] == "ana@example.com"
    assert r.json()["consent_required"] is False

    cookie_header = ";".join(r.headers.get_list("set-cookie"))
    assert f"{SESSION_COOKIE}=" in cookie_header
    assert "HttpOnly" in cookie_header and "Secure" in cookie_header
    assert "samesite=lax" in cookie_header.lower()

    consent = db.scalar(select(Consent))
    assert consent is not None and consent.policy_version == PRIVACY_POLICY_VERSION
    # Only the token hash is stored, never the raw token.
    stored = db.scalar(select(UserSession.token_hash))
    assert stored != client.cookies[SESSION_COOKIE]


def test_register_requires_explicit_consent(client):
    assert register(client, consent=False).status_code == 422
    body = {"email": "x@example.com", "password": PASSWORD}
    assert client.post(f"{API}/auth/register", json=body).status_code == 422


def test_register_rejects_duplicate_email_case_insensitive(client):
    assert register(client).status_code == 201
    assert (
        register(
            TestClient(client.app, base_url="https://testserver"), "ANA@example.com"
        ).status_code
        == 409
    )


def test_register_validates_password_length(client):
    body = {"email": "a@example.com", "password": "short", "consent": True}
    assert client.post(f"{API}/auth/register", json=body).status_code == 422


def test_login_and_me(client, make_user):
    make_user("ion@example.com")
    r = client.post(f"{API}/auth/login", json={"email": "ion@example.com", "password": PASSWORD})
    assert r.status_code == 200
    assert client.get(f"{API}/auth/me").json()["email"] == "ion@example.com"


def test_login_wrong_password(client, make_user):
    make_user("ion@example.com")
    r = client.post(
        f"{API}/auth/login", json={"email": "ion@example.com", "password": "gresit-123456"}
    )
    assert r.status_code == 401


def test_login_is_rate_limited(client, make_user):
    make_user("ion@example.com")
    bad = {"email": "ion@example.com", "password": "gresit-123456"}
    codes = [client.post(f"{API}/auth/login", json=bad).status_code for _ in range(6)]
    assert codes[:5] == [401] * 5
    assert codes[5] == 429


def test_me_requires_session(client):
    assert client.get(f"{API}/auth/me").status_code == 401


def test_logout_invalidates_session(make_user):
    c = make_user()
    token = c.cookies[SESSION_COOKIE]
    assert c.post(f"{API}/auth/logout").status_code == 204
    c.cookies.set(SESSION_COOKIE, token)  # replaying the old token must not work
    assert c.get(f"{API}/auth/me").status_code == 401


def test_unsafe_request_without_csrf_token_is_rejected(make_user):
    c = make_user()
    del c.headers[CSRF_HEADER]
    assert c.post(f"{API}/auth/logout").status_code == 403


def test_request_from_foreign_origin_is_rejected(client):
    r = client.post(
        f"{API}/auth/login",
        json={"email": "a@example.com", "password": PASSWORD},
        headers={"Origin": "https://evil.example"},
    )
    assert r.status_code == 403


def test_consent_required_for_new_policy_version(make_user, db: Session):
    c = make_user()
    db.execute(delete(Consent))
    assert c.get(f"{API}/auth/me").json()["consent_required"] is True
    assert c.post(f"{API}/auth/consent", json={"accepted": False}).status_code == 422
    assert c.post(f"{API}/auth/consent", json={"accepted": True}).status_code == 204
    assert c.get(f"{API}/auth/me").json()["consent_required"] is False


def test_password_change_invalidates_all_other_sessions(app, make_user):
    c = make_user("ion@example.com")
    other = TestClient(app, base_url="https://testserver")
    other.post(f"{API}/auth/login", json={"email": "ion@example.com", "password": PASSWORD})
    assert other.get(f"{API}/auth/me").status_code == 200

    r = c.post(
        f"{API}/auth/password",
        json={"current_password": PASSWORD, "new_password": "parola-noua-456"},
    )
    assert r.status_code == 204
    assert other.get(f"{API}/auth/me").status_code == 401
    assert with_csrf(c).get(f"{API}/auth/me").status_code == 200


def test_password_change_requires_current_password(make_user):
    c = make_user()
    r = c.post(
        f"{API}/auth/password",
        json={"current_password": "gresit-123456", "new_password": "parola-noua-456"},
    )
    assert r.status_code == 403


def test_delete_account_removes_all_user_data(make_user, db: Session):
    c = make_user("ion@example.com")
    keep = make_user("maria@example.com")
    assert c.request("DELETE", f"{API}/account", json={"password": "gresit"}).status_code == 403
    assert c.request("DELETE", f"{API}/account", json={"password": PASSWORD}).status_code == 204

    assert db.scalar(select(User).where(User.email == "ion@example.com")) is None
    assert db.scalar(select(func.count()).select_from(UserSession)) == 1
    assert db.scalar(select(func.count()).select_from(Consent)) == 1
    assert keep.get(f"{API}/auth/me").status_code == 200


def test_export_returns_own_data(make_user):
    c = make_user("ion@example.com")
    data = c.get(f"{API}/account/export").json()
    assert data["email"] == "ion@example.com"
    assert data["consents"][0]["policy_version"] == PRIVACY_POLICY_VERSION


def test_security_headers_and_health(client):
    r = client.get("/api/health")
    assert r.json() == {"status": "ok"}
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["cache-control"] == "no-store"
