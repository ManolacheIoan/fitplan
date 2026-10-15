"""HTTP hardening: security headers and CSRF protection.

CSRF uses two layers for unsafe methods (POST/PUT/PATCH/DELETE):
1. If the browser sends an Origin header, it must be in ALLOWED_ORIGINS.
2. If a session cookie is present, the X-CSRF-Token header must equal
   HMAC(SECRET_KEY, session token). The frontend reads that value from the
   non-HttpOnly CSRF cookie set at login (double-submit, bound to the session).
"""

import hashlib
import hmac
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.config import get_settings

SESSION_COOKIE = "fitplan_session"
CSRF_COOKIE = "fitplan_csrf"
CSRF_HEADER = "X-CSRF-Token"
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    # API responses contain personal data: never cache them (also covers the Netlify proxy).
    "Cache-Control": "no-store",
}

Handler = Callable[[Request], Awaitable[Response]]


def csrf_token_for(session_token: str) -> str:
    key = get_settings().secret_key.encode()
    return hmac.new(key, session_token.encode(), hashlib.sha256).hexdigest()


def _csrf_error() -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": "csrf_failed"})


async def csrf_middleware(request: Request, call_next: Handler) -> Response:
    if request.method in UNSAFE_METHODS:
        origin = request.headers.get("origin")
        if origin is not None and origin.rstrip("/") not in get_settings().allowed_origins:
            return _csrf_error()
        session_token = request.cookies.get(SESSION_COOKIE)
        if session_token:
            sent = request.headers.get(CSRF_HEADER, "")
            if not hmac.compare_digest(sent, csrf_token_for(session_token)):
                return _csrf_error()
    return await call_next(request)


async def security_headers_middleware(request: Request, call_next: Handler) -> Response:
    response = await call_next(request)
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    return response
