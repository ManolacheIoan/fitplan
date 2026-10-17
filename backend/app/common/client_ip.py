"""Client IP for rate limiting, read only from hops added by trusted proxies.

X-Forwarded-For is a list that every proxy appends to; everything left of the entries our
own proxies added is whatever the client chose to send. With TRUSTED_PROXY_HOPS = n, the
client IP is the n-th entry from the right. With 0 (local development, tests) the header is
ignored and the socket peer is used. See DECISIONS.md for the production chain.
"""

from fastapi import Request

from app.config import get_settings


def client_ip(request: Request) -> str:
    peer = request.client.host if request.client else "unknown"
    hops = get_settings().trusted_proxy_hops
    if hops == 0:
        return peer
    # Several X-Forwarded-For headers are equivalent to one comma-joined list.
    joined = ",".join(request.headers.getlist("x-forwarded-for"))
    entries = [entry.strip() for entry in joined.split(",") if entry.strip()]
    if len(entries) < hops:
        # The trusted proxies always add their hops, so this is a misconfiguration.
        # The socket peer is not client-controlled, so it is a safe fallback.
        return peer
    return entries[-hops]
