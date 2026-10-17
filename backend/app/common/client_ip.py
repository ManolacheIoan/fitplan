"""Client IP for rate limiting. See DECISIONS.md for the trust model.

1. Requests that carry the Netlify proxy secret (PROXY_SECRET, compared in constant time)
   came through our Netlify proxy rule. For them, the visitor's address is read from
   `X-Nf-Client-Connection-Ip`, which Netlify sets from the connection it accepted.
2. Every other request (direct calls to Render, a wrong or missing secret) cannot choose
   its address: we use the connecting IP, which is the X-Forwarded-For entry added by
   Render (TRUSTED_PROXY_HOPS from the right), or the socket peer when that is 0.
3. A proxied request whose visitor header is missing or invalid falls back to the
   connecting IP, which is then a Netlify address shared by many visitors (`shared`).
"""

import hmac
import ipaddress
import logging
from dataclasses import dataclass

from fastapi import Request

from app.config import get_settings

PROXY_SECRET_HEADER = "x-fitplan-proxy-secret"  # noqa: S105 (a header name, not a secret)
NETLIFY_CLIENT_IP_HEADER = "x-nf-client-connection-ip"

logger = logging.getLogger("fitplan.client_ip")


@dataclass(frozen=True)
class ClientIP:
    address: str
    # How the address was obtained: "netlify" (visitor header behind a valid secret),
    # "netlify-fallback" (valid secret, no usable visitor header) or "direct".
    source: str

    @property
    def shared(self) -> bool:
        """The address belongs to the proxy, not to one visitor: per-IP limits would be
        shared by everyone behind it, so callers must not apply them."""
        return self.source == "netlify-fallback"


def connecting_ip(request: Request) -> str:
    """The address that connected to our infrastructure; never client-controlled."""
    peer = request.client.host if request.client else "unknown"
    hops = get_settings().trusted_proxy_hops
    if hops == 0:
        return peer
    # Several X-Forwarded-For headers are equivalent to one comma-joined list.
    joined = ",".join(request.headers.getlist("x-forwarded-for"))
    entries = [entry.strip() for entry in joined.split(",") if entry.strip()]
    # Fewer entries than trusted hops is a misconfiguration; the socket peer is safe.
    return entries[-hops] if len(entries) >= hops else peer


def _has_proxy_secret(request: Request) -> bool:
    expected = get_settings().proxy_secret
    if not expected:
        return False
    # Whether Netlify replaces or appends a client-sent copy is undocumented: accept the
    # request if any copy matches (a client cannot know the value anyway).
    sent = request.headers.getlist(PROXY_SECRET_HEADER)
    return any(hmac.compare_digest(value.encode(), expected.encode()) for value in sent)


def _visitor_ip(request: Request) -> str | None:
    values = request.headers.getlist(NETLIFY_CLIENT_IP_HEADER)
    # Several copies would mean a client-sent value next to Netlify's: trust none of them.
    if len(values) != 1:
        return None
    try:
        return str(ipaddress.ip_address(values[0].strip()))
    except ValueError:
        return None


def _masked(address: str) -> str:
    """/24 (IPv4) or /48 (IPv6) prefix: enough to recognise your own network in a log."""
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return "invalid"
    prefix = 24 if ip.version == 4 else 48
    return str(ipaddress.ip_network(f"{ip}/{prefix}", strict=False))


def client_ip(request: Request) -> ClientIP:
    if _has_proxy_secret(request):
        visitor = _visitor_ip(request)
        result = (
            ClientIP(visitor, "netlify")
            if visitor
            else ClientIP(connecting_ip(request), "netlify-fallback")
        )
    else:
        result = ClientIP(connecting_ip(request), "direct")
    if get_settings().log_client_ip_resolution:
        # Deploy verification only (README checklist); off by default. Masked address.
        logger.warning("client_ip source=%s prefix=%s", result.source, _masked(result.address))
    return result
