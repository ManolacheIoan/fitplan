"""In-memory sliding-window rate limiter.

Good enough for a single free-tier instance; counters reset when the process restarts.
With several instances this would need a shared store (e.g. Redis). Keys (IPs, emails)
are dropped by `prune` once they have no hit left in the window.
"""

import time
import weakref
from collections import defaultdict, deque
from threading import Lock

_instances: "weakref.WeakSet[RateLimiter]" = weakref.WeakSet()


def prune_all() -> None:
    for limiter in list(_instances):
        limiter.prune()


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()
        _instances.add(self)

    def hit(self, key: str) -> bool:
        """Record an attempt for `key`; return False if the limit is exceeded."""
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] <= now - self.window_seconds:
                hits.popleft()
            if len(hits) >= self.limit:
                return False
            hits.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    def prune(self) -> None:
        """Forget keys whose hits are all outside the window."""
        cutoff = time.monotonic() - self.window_seconds
        with self._lock:
            for key in [k for k, hits in self._hits.items() if not hits or hits[-1] <= cutoff]:
                del self._hits[key]

    def __len__(self) -> int:
        return len(self._hits)
