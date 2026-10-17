"""No health values in logs, and in-memory state does not outlive its TTL."""

import logging
import threading

from fastapi import APIRouter
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.common.db import get_engine
from app.common.housekeeping import PRUNE_INTERVAL_SECONDS, Housekeeper
from app.common.rate_limit import RateLimiter
from app.main import create_app
from app.nutrition import service as nutrition_service


def test_engine_hides_sql_parameters():
    assert get_engine().hide_parameters is True


def _app_with_failing_route():
    router = APIRouter()

    @router.post("/boom/{item_id}")
    def boom(item_id: int) -> None:
        with get_engine().connect() as conn:
            conn.execute(text("CREATE TEMP TABLE t (w numeric CHECK (w < 10))"))
            conn.execute(text("INSERT INTO t VALUES (:w)"), {"w": 58.7})

    app = create_app()
    app.include_router(router)
    return app


def test_unhandled_errors_are_logged_without_values(caplog):
    client = TestClient(_app_with_failing_route(), raise_server_exceptions=False)
    with caplog.at_level(logging.DEBUG):
        r = client.post("/boom/4242")
    assert r.status_code == 500 and r.json() == {"detail": "internal_error"}
    assert r.headers["cache-control"] == "no-store"
    # httpx is the test client's own logger (it prints the URL it requested).
    logged = "\n".join(r.getMessage() for r in caplog.records if r.name != "httpx")
    assert "IntegrityError" in logged and "POST /boom/{item_id}" in logged
    for value in ("58.7", "4242", "Failing row"):
        assert value not in logged


def test_sqlalchemy_does_not_append_bound_parameters():
    # Postgres may still quote a value in its own message, which is why errors are only
    # ever logged through safe_errors_middleware (type and frames, no message).
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT CAST(:v AS int)"), {"v": "secret-73.4"})
    except DBAPIError as exc:
        assert "[SQL parameters hidden due to hide_parameters=True]" in str(exc)
        assert "'secret-73.4'" not in str(exc)


def test_rate_limiter_forgets_keys_after_the_window(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr("app.common.rate_limit.time.monotonic", lambda: now[0])
    limiter = RateLimiter(limit=3, window_seconds=60)
    limiter.hit("ion@example.com|203.0.113.9")
    limiter.hit("203.0.113.10")
    now[0] += 30
    limiter.hit("203.0.113.10")
    now[0] += 31  # first key: last hit 61 s ago; second: 31 s ago
    limiter.prune()
    assert len(limiter) == 1
    now[0] += 30
    limiter.prune()
    assert len(limiter) == 0


def test_searched_terms_are_pruned_within_24_hours(monkeypatch):
    now = [5000.0]
    monkeypatch.setattr("app.nutrition.service.time.monotonic", lambda: now[0])
    nutrition_service._searched_terms[("mock", "iaurt")] = now[0] + (
        nutrition_service.SEARCHED_TERM_TTL_SECONDS
    )
    # TTL plus one housekeeping interval must stay within 24 hours.
    assert nutrition_service.SEARCHED_TERM_TTL_SECONDS + PRUNE_INTERVAL_SECONDS <= 24 * 3600
    now[0] += nutrition_service.SEARCHED_TERM_TTL_SECONDS
    nutrition_service.prune_searched_terms()
    assert ("mock", "iaurt") not in nutrition_service._searched_terms


def test_housekeeper_runs_tasks_and_stops():
    ran = threading.Event()
    keeper = Housekeeper([ran.set], interval=0.01)
    keeper.start()
    assert ran.wait(2)
    keeper.stop()
