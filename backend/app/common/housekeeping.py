"""Background pruning of in-memory state (rate-limiter counters, searched terms).

Runs in a daemon thread so expired entries leave memory on time even without traffic.
"""

import threading
from collections.abc import Callable

PRUNE_INTERVAL_SECONDS = 5 * 60


class Housekeeper:
    def __init__(self, tasks: list[Callable[[], None]], interval: float) -> None:
        self._tasks = tasks
        self._interval = interval
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="housekeeping", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=5)

    def _run(self) -> None:
        while not self._stop.wait(self._interval):
            for task in self._tasks:
                task()
