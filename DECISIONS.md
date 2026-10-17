# Decisions

## Client IP for rate limiting (2026-10-17)

**Decision:** the backend takes the client IP from the **right-most `X-Forwarded-For`
entry** (`TRUSTED_PROXY_HOPS=1` on Render) and ignores everything to its left. uvicorn no
longer runs with `--proxy-headers --forwarded-allow-ips='*'`. Login is limited per
(email, IP) pair and per IP. Registration and guest start are limited per IP.

### The proxy chain

```
Browser ──> Netlify edge (/api/* rewrite, 200!) ──> Render edge proxy ──> uvicorn
attacker ─────────────────────────────────────────> Render edge proxy ──> uvicorn
```

- `X-Forwarded-For` is a list. Each proxy **appends** the address that connected to it.
  The client can pre-fill the list with anything it likes.
- Render's edge does not strip an incoming `X-Forwarded-For`; it appends to it (community
  reports, no official documentation). The public `*.onrender.com` URL is reachable
  directly, so the backend cannot assume traffic came through Netlify.
- Netlify does not publish whether its proxy appends the visitor's IP to
  `X-Forwarded-For` for external origins, and it strips its `X-Nf-*` headers
  (`x-nf-client-connection-ip`) from proxied requests.

### Why the right-most entry

| Entry | Through Netlify | Direct to Render | Spoofable? |
|---|---|---|---|
| left-most (what `--forwarded-allow-ips='*'` used) | client-supplied | client-supplied | **yes** |
| second from the right | the visitor's IP, if Netlify appends it | client-supplied | **yes**, by calling Render directly |
| right-most | Netlify egress IP | the attacker's real IP | no: Render writes it |

Only the right-most entry is written by a proxy we trust on every path. Anything further
left can be forged by skipping Netlify.

### Consequences

- Traffic that comes through Netlify is keyed by the **Netlify egress IP**, which many
  visitors share. That is why login has a separate, higher per-IP limit
  (`LOGIN_IP_RATE_LIMIT=20`) and a per-(email, IP) limit
  (`LOGIN_RATE_LIMIT=5`). Registration and guest start stay at 5 per IP per window, so
  busy periods may see `429 too_many_attempts` on sign-up. Raise the limit if that happens.
- Direct calls to Render are keyed by the caller's real address and can no longer
  rotate a forged header to get unlimited attempts.
- A stranger can no longer lock an owner out. Failed attempts from the stranger's IP
  only block that (email, IP) pair, not the account.
- If `X-Forwarded-For` has fewer entries than `TRUSTED_PROXY_HOPS` (misconfiguration), the
  socket peer is used. It is not client-controlled either.

### To verify and how to improve

- **Not verified on the live deployment.** Render's header behaviour comes from its
  community forum, not from its docs. Before relying on it, confirm the hop count with
  Render support or a one-off header dump on a staging service. If Render adds more than
  one hop (for example a CDN layer and a load balancer), the right-most entry is still
  not spoofable but is shared more widely. Keep `TRUSTED_PROXY_HOPS=1` in that case.
- To key on the visitor's real IP behind Netlify, the backend would need proof that a
  request came through Netlify, for example Netlify's signed proxy redirects
  (`x-nf-sign`, HS256 JWS). Only then could it trust the entry Netlify adds
  (`TRUSTED_PROXY_HOPS=2`), and only if Netlify really appends it. Not implemented.
- The limiter is in memory (one instance, reset on restart).
