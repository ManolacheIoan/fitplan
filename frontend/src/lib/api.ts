/**
 * Same-origin API client. In production Netlify proxies /api/* to the backend, so the
 * session cookie is first-party. Route guards in the UI are only UX: the API enforces
 * every authorization rule.
 *
 * Cold starts: free-tier backends sleep when idle and may need 30-60 s to wake, longer
 * than the proxy timeout. Before talking to a possibly sleeping backend we poll the cheap
 * /api/health endpoint with backoff, so a non-idempotent request (POST etc.) is never
 * sent twice. GET requests are additionally retried on gateway errors.
 */

const CSRF_COOKIE = "fitplan_csrf";
const RETRY_STATUSES = new Set([502, 503, 504]);
const BACKOFF_MS = [1000, 2000, 4000, 8000, 15000, 15000];
// Render's free tier sleeps after ~15 min idle; re-check well before that.
const AWAKE_FOR_MS = 10 * 60 * 1000;

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: unknown,
  ) {
    super(typeof detail === "string" ? detail : `HTTP ${status}`);
  }
}

// --- "server is waking up" signal, consumed by <WakeBanner /> ---------------------------
type Listener = (waking: boolean) => void;
const listeners = new Set<Listener>();
export function onWakingChange(listener: Listener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
function setWaking(waking: boolean) {
  listeners.forEach((l) => l(waking));
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

let lastOkAt = 0;
let wakePromise: Promise<void> | null = null;

async function wakeBackend(): Promise<void> {
  // A healthy backend answers in milliseconds; show the banner only if it is slow.
  const bannerTimer = setTimeout(() => setWaking(true), 1500);
  try {
    for (let attempt = 0; ; attempt++) {
      try {
        const res = await fetch("/api/health", {
          cache: "no-store",
          signal: AbortSignal.timeout(10_000),
        });
        if (res.ok) {
          lastOkAt = Date.now();
          return;
        }
      } catch {
        // network error or timeout while the backend is starting: retry below
      }
      if (attempt >= BACKOFF_MS.length) throw new ApiError(503, "backend_unavailable");
      await sleep(BACKOFF_MS[attempt]);
    }
  } finally {
    clearTimeout(bannerTimer);
  }
}

export async function ensureAwake(): Promise<void> {
  if (Date.now() - lastOkAt < AWAKE_FOR_MS) return;
  wakePromise ??= wakeBackend().finally(() => {
    wakePromise = null;
    setWaking(false);
  });
  return wakePromise;
}

function readCookie(name: string): string | undefined {
  return document.cookie
    .split("; ")
    .find((c) => c.startsWith(`${name}=`))
    ?.slice(name.length + 1);
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  await ensureAwake();
  const method = (init.method ?? "GET").toUpperCase();
  const headers = new Headers(init.headers);
  if (init.body !== undefined) headers.set("Content-Type", "application/json");
  if (method !== "GET") {
    const csrf = readCookie(CSRF_COOKIE);
    if (csrf) headers.set("X-CSRF-Token", csrf);
  }

  const retries = method === "GET" ? BACKOFF_MS.length : 0;
  for (let attempt = 0; ; attempt++) {
    const res = await fetch(`/api/v1${path}`, {
      ...init,
      method,
      headers,
      credentials: "same-origin",
      cache: "no-store",
    });
    if (RETRY_STATUSES.has(res.status) && attempt < retries) {
      setWaking(true);
      await sleep(BACKOFF_MS[attempt]);
      continue;
    }
    setWaking(false);
    if (res.ok) lastOkAt = Date.now();
    if (res.status === 204) return undefined as T;
    const body = await res.json().catch(() => null);
    if (!res.ok) throw new ApiError(res.status, body?.detail ?? null);
    return body as T;
  }
}

export const json = (data: unknown): Pick<RequestInit, "body"> => ({ body: JSON.stringify(data) });
