"""Client IP trust model (DECISIONS.md): only requests carrying the Netlify proxy secret may
name the visitor's IP; nobody can choose their address through X-Forwarded-For."""

import pytest
from starlette.requests import Request

from app.auth import router as auth_router
from app.common.client_ip import NETLIFY_CLIENT_IP_HEADER, PROXY_SECRET_HEADER, client_ip
from app.config import Settings, get_settings
from tests.conftest import PASSWORD
from tests.factories import API

SECRET = "s3cret-" + "x" * 40
NETLIFY_EGRESS = "198.51.100.1"  # appended by Render for every request Netlify forwards
BAD = {"email": "ion@example.com", "password": "gresit-123456"}


@pytest.fixture(autouse=True)
def production_like(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "trusted_proxy_hops", 1)
    monkeypatch.setattr(settings, "proxy_secret", SECRET)


def via_netlify(visitor: str | None, xff: str = "", secret: str = SECRET) -> dict[str, str]:
    """Headers as they reach the backend through the Netlify proxy rule."""
    headers = {PROXY_SECRET_HEADER: secret, "X-Forwarded-For": f"{xff}{NETLIFY_EGRESS}"}
    if visitor is not None:
        headers[NETLIFY_CLIENT_IP_HEADER] = visitor
    return headers


def direct(real_ip: str, xff: str = "", **extra: str) -> dict[str, str]:
    """Headers of a request sent straight to Render (Render appends the real address)."""
    return {"X-Forwarded-For": f"{xff}{real_ip}", **extra}


def resolve(headers: dict[str, str]):
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        "client": ("10.0.0.2", 443),  # Render's internal proxy
    }
    return client_ip(Request(scope))


def login(client, headers: dict[str, str], **body):
    return client.post(f"{API}/auth/login", json=body or BAD, headers=headers)


def register(client, email: str, headers: dict[str, str]):
    client.cookies.clear()  # each attempt as a fresh visitor
    body = {"email": email, "password": PASSWORD, "consent": True}
    return client.post(f"{API}/auth/register", json=body, headers=headers)


# --- Resolution ----------------------------------------------------------------------------


def test_spoofed_forwarded_for_without_secret_uses_the_connecting_ip():
    ip = resolve(direct("203.0.113.9", xff="1.2.3.4, 5.6.7.8, "))
    assert (ip.address, ip.source, ip.shared) == ("203.0.113.9", "direct", False)


def test_forged_netlify_header_without_secret_is_ignored():
    ip = resolve(direct("203.0.113.9", **{NETLIFY_CLIENT_IP_HEADER: "8.8.8.8"}))
    assert ip.address == "203.0.113.9" and ip.source == "direct"


def test_wrong_secret_is_treated_as_a_direct_request():
    for wrong in ("nope", SECRET[:-1], SECRET + "x", SECRET.upper()):
        ip = resolve(via_netlify("8.8.8.8", secret=wrong))
        assert (ip.address, ip.source) == (NETLIFY_EGRESS, "direct")


def test_valid_secret_uses_the_netlify_visitor_header_and_ignores_forwarded_for():
    ip = resolve(via_netlify("203.0.113.77", xff="1.2.3.4, "))
    assert (ip.address, ip.source, ip.shared) == ("203.0.113.77", "netlify", False)


def test_valid_secret_without_visitor_header_falls_back_to_the_shared_proxy_ip():
    for visitor in (None, "", "not-an-ip", "1.2.3.4, 5.6.7.8"):
        ip = resolve(via_netlify(visitor, xff="1.2.3.4, "))
        assert (ip.address, ip.source, ip.shared) == (NETLIFY_EGRESS, "netlify-fallback", True)


def _scope_request(headers: list[tuple[str, str]]):
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/",
        "headers": [(k.encode(), v.encode()) for k, v in headers],
        "client": ("10.0.0.2", 443),
    }
    return client_ip(Request(scope))


def test_secret_accepted_when_a_client_copy_comes_first():
    ip = _scope_request(
        [
            (PROXY_SECRET_HEADER, "guess"),
            (PROXY_SECRET_HEADER, SECRET),
            (NETLIFY_CLIENT_IP_HEADER, "203.0.113.77"),
            ("x-forwarded-for", NETLIFY_EGRESS),
        ]
    )
    assert (ip.address, ip.source) == ("203.0.113.77", "netlify")


def test_duplicated_visitor_header_is_not_trusted():
    ip = _scope_request(
        [
            (PROXY_SECRET_HEADER, SECRET),
            (NETLIFY_CLIENT_IP_HEADER, "8.8.8.8"),  # client-sent copy
            (NETLIFY_CLIENT_IP_HEADER, "203.0.113.77"),
            ("x-forwarded-for", NETLIFY_EGRESS),
        ]
    )
    assert (ip.address, ip.source) == (NETLIFY_EGRESS, "netlify-fallback")


def test_ipv6_visitor_is_normalized():
    assert resolve(via_netlify("2001:DB8::1")).address == "2001:db8::1"


def test_no_secret_configured_means_nobody_can_name_an_ip(monkeypatch):
    monkeypatch.setattr(get_settings(), "proxy_secret", "")
    ip = resolve({PROXY_SECRET_HEADER: "", NETLIFY_CLIENT_IP_HEADER: "8.8.8.8"})
    assert ip.source == "direct"


def test_short_proxy_secret_is_rejected():
    with pytest.raises(ValueError):
        Settings(database_url="postgresql://x", secret_key="k", proxy_secret="short")


# --- Limits ----------------------------------------------------------------------------------


def test_spoofed_forwarded_for_without_secret_does_not_bypass_the_limit(client, make_user):
    make_user("ion@example.com")
    codes = [
        login(client, direct("203.0.113.9", xff=f"10.0.0.{i}, ")).status_code for i in range(6)
    ]
    assert codes[:5] == [401] * 5 and codes[5] == 429


def test_spoofed_forwarded_for_with_secret_does_not_bypass_the_limit(client, make_user):
    make_user("ion@example.com")
    headers = [via_netlify("203.0.113.9", xff=f"10.0.0.{i}, ") for i in range(6)]
    codes = [login(client, h).status_code for h in headers]
    assert codes[:5] == [401] * 5 and codes[5] == 429


def test_wrong_secret_cannot_rotate_visitor_ips(client, make_user):
    make_user("ion@example.com")
    headers = [via_netlify(f"203.0.113.{i}", secret="wrong" * 10) for i in range(6)]
    codes = [login(client, h).status_code for h in headers]
    assert codes[5] == 429  # all counted against the connecting address


def test_stranger_cannot_lock_the_owner_out(client, make_user):
    make_user("ion@example.com")
    for _ in range(10):
        login(client, via_netlify("203.0.113.66"))
    owner = {"email": "ion@example.com", "password": PASSWORD}
    assert login(client, via_netlify("198.51.100.7"), **owner).status_code == 200


def test_many_visitors_behind_one_proxy_ip_are_limited_separately(client):
    # 40 visitors, all forwarded by the same Netlify egress address.
    for i in range(40):
        r = register(client, f"v{i}@example.com", via_netlify(f"203.0.113.{i + 1}"))
        assert r.status_code == 201, (i, r.text)
    for i in range(40):
        body = {"email": f"v{i}@example.com", "password": PASSWORD}
        client.cookies.clear()
        assert login(client, via_netlify(f"203.0.113.{i + 1}"), **body).status_code == 200


def test_without_visitor_header_one_visitor_cannot_block_sign_ups_for_everyone(client):
    # Fallback: everyone shares the proxy address, so no per-IP limit applies to it.
    codes = [register(client, f"f{i}@example.com", via_netlify(None)).status_code for i in range(8)]
    assert codes == [201] * 8


def test_one_visitor_cannot_exhaust_the_global_limit(client, monkeypatch):
    monkeypatch.setattr(auth_router.auth_global_limiter, "limit", 30)
    attacker = via_netlify("203.0.113.66")
    codes = [
        login(client, attacker, email=f"x{i}@example.com", password="x").status_code
        for i in range(100)
    ]
    ip_limit = get_settings().login_ip_rate_limit
    assert codes.count(401) == ip_limit and set(codes[ip_limit:]) == {429}
    # Only the attacker's 20 allowed attempts were counted globally: others still get in.
    r = register(client, "legit@example.com", via_netlify("198.51.100.42"))
    assert r.status_code == 201


def test_global_soft_limit_answers_with_a_clear_code(client, monkeypatch):
    monkeypatch.setattr(auth_router.auth_global_limiter, "limit", 3)
    codes = []
    for i in range(4):
        r = register(client, f"g{i}@example.com", via_netlify(f"203.0.113.{i + 1}"))
        codes.append(r.status_code)
    assert codes == [201, 201, 201, 429]
    assert r.json()["detail"] == "auth_busy" and int(r.headers["retry-after"]) > 0


def test_resolution_log_is_masked_and_off_by_default(client, caplog, monkeypatch):
    login(client, via_netlify("203.0.113.77"))
    assert "client_ip" not in caplog.text
    monkeypatch.setattr(get_settings(), "log_client_ip_resolution", True)
    login(client, via_netlify("203.0.113.77"))
    assert "source=netlify prefix=203.0.113.0/24" in caplog.text
    assert "203.0.113.77" not in caplog.text.replace("httpx", "")
