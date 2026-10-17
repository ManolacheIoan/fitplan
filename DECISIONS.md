# Decisions

## Client IP for rate limiting (2026-10-17, revised the same day)

**Decision:** a request may name the visitor's IP only when it carries the Netlify proxy
secret. Every other request is keyed by the address that connected to Render, which the
client cannot choose. Per-visitor limits are backed by a global soft limit.

### The proxy chain

```
Browser ──> Netlify edge (/api/* proxy rule) ──> Render edge proxy ──> uvicorn
attacker ──────────────────────────────────────> Render edge proxy ──> uvicorn
```

The public `*.onrender.com` URL is reachable directly, so the backend cannot assume a
request came through Netlify. `X-Forwarded-For` is a list that every proxy appends to, and
the client can pre-fill it with anything. Nothing in it is trusted except the entry
Render adds.

### How the client IP is resolved (`backend/app/common/client_ip.py`)

| Request | Client IP used | `source` |
|---|---|---|
| Carries `X-FitPlan-Proxy-Secret` equal to `PROXY_SECRET` (constant-time comparison) and exactly one valid `X-Nf-Client-Connection-Ip` | that header | `netlify` |
| Valid secret, but the visitor header is missing, invalid or duplicated | connecting IP (a Netlify address, **shared**) | `netlify-fallback` |
| No secret, wrong secret, or `PROXY_SECRET` unset | connecting IP | `direct` |

- **Connecting IP:** the `TRUSTED_PROXY_HOPS`-th `X-Forwarded-For` entry from the right
  (`1` on Render: the entry Render appends), or the socket peer when the setting is `0`
  (local development, tests). The socket peer on Render is Render's own proxy, so "the
  direct connection IP" in practice means the address Render saw.
- **The secret:** Netlify sends it as a custom header on the proxy rule in
  `frontend/netlify.toml`. netlify.toml cannot read environment variables, but Netlify
  reads `[[redirects]]` only after the build command. So
  `frontend/scripts/configure-proxy.mjs` substitutes `BACKEND_URL` and `PROXY_SECRET` from
  the Netlify environment into the rule during the build. This is the documented method
  ([File-based configuration → Inject environment variable values](https://docs.netlify.com/build/configure-builds/file-based-configuration/#inject-environment-variable-values),
  [custom headers in proxy redirects](https://docs.netlify.com/manage/routing/redirects/rewrites-proxies/#custom-headers-in-proxy-redirects)).
  The same value is set as `PROXY_SECRET` on Render. It is at least 32 characters, and the
  backend refuses to start with a shorter one.
- If Netlify appended a client-sent copy of the secret header instead of replacing it, any
  matching copy is accepted, because a client cannot know the value. If the visitor header
  arrives more than once, a client-sent copy may be among them, so none is trusted.

### Which header carries the visitor IP (not fully verified)

`X-Nf-Client-Connection-Ip` is **not documented in Netlify's docs for proxy requests**.
The source is a Netlify staff announcement on the support forum (2022-02-28, "Stripping
exposed Netlify headers from function and proxy requests"). It removes `X-Nf-*` headers
from function and external proxy requests **except** `X-Nf-Client-Connection-Ip`,
`X-Nf-Request-Id` and `X-Nf-Sign`. A staff reply on 2022-03-01 calls it "the right one
for inspecting the connecting IP address"
([thread](https://answers.netlify.com/t/upcoming-change-stripping-exposed-netlify-headers-from-function-and-proxy-requests/52665)).
Other staff replies (2023) point to `X-Forwarded-For`, which a client can pre-fill, so it
is not used.

Because this is not confirmed for our setup, the code uses the **safest fallback** when
the header is absent: the shared Netlify address, flagged `netlify-fallback`. It never
reads `X-Forwarded-For` for the visitor. The README deploy checklist verifies the header
on the live deployment.

### Limits (`backend/app/auth/router.py`)

| Limit | Key | Default | Applied when |
|---|---|---|---|
| Login per account and visitor | (email, client IP) | 5 / 15 min | always |
| Login per visitor | client IP | 20 / 15 min | not `netlify-fallback` |
| Registration + guest start per visitor | client IP | 5 / 15 min | not `netlify-fallback` |
| **Global soft limit** | whole app (login + registration + guest) | 300 / 15 min (`AUTH_GLOBAL_LIMIT`) | always, counted last |

- Checks stop at the first refusal. Only attempts that passed the per-visitor limits count
  towards the global limit, so one visitor can add at most 20 login and 5 sign-up attempts
  per window. It cannot exhaust the global limit alone.
- When the global limit is reached, the API answers `429 auth_busy` with `Retry-After`.
  The UI says that authentication is busy and to try again in a few minutes.
- A stranger's failed logins only block their own (email, IP) pair, so they cannot lock
  the owner out.

### Tradeoffs

- **Distributed abuse vs. availability.** About a dozen visitors with distinct real IPs,
  each using their full quota, can reach the global limit. Logins and sign-ups for
  everyone then pause until the window frees up (at most 15 minutes, with a clear message).
  That is the price of a backstop against credential stuffing from many addresses. Raise
  `AUTH_GLOBAL_LIMIT` if legitimate peaks reach it.
- **Fallback mode.** If the visitor header is missing, every visitor behind Netlify shares
  one address. Per-IP limits are then skipped so that one visitor cannot block everyone.
  Only the (email, IP) and global limits apply, and the (email, IP) key is effectively
  per email: in that mode, someone repeatedly failing logins for an email delays its owner too.
- **Shared networks.** Visitors behind one NAT (office, mobile carrier) share the 20 login
  and 5 sign-up attempts per window.
- **In memory, single instance.** Counters reset on restart and do not work across
  several instances.
- **Secret handling.** The secret ends up in Netlify's processed deploy configuration
  (not in the published files, not in git). Rotating it needs a Render env change plus a
  Netlify rebuild, and logins via Netlify fall back to `direct` keys in between.

### Verification support

`LOG_CLIENT_IP_RESOLUTION=true` logs one line per auth request: `source` and the address
masked to /24 (IPv4) or /48 (IPv6). It is for the deploy check only and is off by default,
so no addresses are written to logs in normal operation.
