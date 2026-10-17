"""Rate limiting must not be bypassable with a forged X-Forwarded-For header."""

import pytest

from app.config import get_settings
from tests.conftest import PASSWORD
from tests.factories import API

BAD = {"email": "ion@example.com", "password": "gresit-123456"}


@pytest.fixture
def behind_render(monkeypatch):
    # Production: one trusted hop (Render's proxy appends the address that connected to it).
    monkeypatch.setattr(get_settings(), "trusted_proxy_hops", 1)


def login(client, xff: str | None = None, **body):
    headers = {"X-Forwarded-For": xff} if xff is not None else {}
    return client.post(f"{API}/auth/login", json=body or BAD, headers=headers)


def test_spoofed_left_most_values_do_not_bypass_the_limit(client, make_user, behind_render):
    make_user("ion@example.com")
    # The attacker rotates the value it controls; Render appends the real 203.0.113.9.
    codes = [login(client, f"10.0.0.{i}, 203.0.113.9").status_code for i in range(6)]
    assert codes[:5] == [401] * 5 and codes[5] == 429


def test_header_is_ignored_without_trusted_hops(client, make_user):
    make_user("ion@example.com")
    codes = [login(client, f"198.51.100.{i}").status_code for i in range(6)]
    assert codes[5] == 429  # every request counted against the socket peer


def test_multiple_forwarded_headers_use_the_last_trusted_hop(client, make_user, behind_render):
    make_user("ion@example.com")
    for i in range(5):
        headers = [("x-forwarded-for", f"10.9.9.{i}"), ("x-forwarded-for", "203.0.113.9")]
        client.post(f"{API}/auth/login", json=BAD, headers=headers)
    assert login(client, "1.2.3.4, 203.0.113.9").status_code == 429


def test_stranger_cannot_lock_the_owner_out(client, make_user, behind_render):
    make_user("ion@example.com")
    for _ in range(10):
        login(client, "203.0.113.66")  # attacker's real address
    owner = {"email": "ion@example.com", "password": PASSWORD}
    assert login(client, "198.51.100.7", **owner).status_code == 200


def test_spraying_many_emails_from_one_ip_is_capped(client, behind_render):
    limit = get_settings().login_ip_rate_limit
    codes = [
        login(client, "203.0.113.5", email=f"u{i}@example.com", password="x").status_code
        for i in range(limit + 1)
    ]
    assert set(codes[:limit]) == {401} and codes[limit] == 429


def test_registration_limit_cannot_be_bypassed_by_spoofing(client, behind_render):
    codes = []
    for i in range(6):
        body = {"email": f"new{i}@example.com", "password": PASSWORD, "consent": True}
        headers = {"X-Forwarded-For": f"10.1.1.{i}, 203.0.113.9"}
        client.cookies.clear()  # each attempt as a fresh visitor
        codes.append(client.post(f"{API}/auth/register", json=body, headers=headers).status_code)
    assert codes[:5] == [201] * 5 and codes[5] == 429
