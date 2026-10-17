"""Test setup: a real PostgreSQL test database, migrated once per run.

Each test runs inside a transaction that is rolled back afterwards; application
commits only release SAVEPOINTs, so tests are isolated and fast.
"""

import os
from collections.abc import Callable, Iterator

os.environ.setdefault(
    "TEST_DATABASE_URL", "postgresql+psycopg://fitplan:fitplan@localhost:5433/fitplan_test"
)
os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
os.environ.setdefault("SECRET_KEY", "test-secret")
# Tests never call external services, whatever the local .env says.
os.environ["FOOD_SOURCE"] = "none"

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.router import login_ip_limiter, login_limiter, register_limiter
from app.common.db import get_db, get_engine
from app.common.security import CSRF_COOKIE, CSRF_HEADER
from app.main import create_app
from app.nutrition.service import reset_external_search_state
from seed.__main__ import seed_exercises, seed_foods

API = "/api/v1"
PASSWORD = "parola-sigura-123"


@pytest.fixture(scope="session", autouse=True)
def _migrated_database() -> None:
    with get_engine().begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public"))
    command.upgrade(Config("alembic.ini"), "head")
    with Session(get_engine()) as session:
        seed_exercises(session)
        seed_foods(session)
        session.commit()


@pytest.fixture
def db() -> Iterator[Session]:
    connection = get_engine().connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(autouse=True)
def _reset_rate_limits() -> None:
    login_limiter.reset()
    login_ip_limiter.reset()
    register_limiter.reset()
    reset_external_search_state()


@pytest.fixture
def app(db: Session):
    application = create_app()
    application.dependency_overrides[get_db] = lambda: db
    return application


@pytest.fixture
def client(app) -> TestClient:
    # https base URL so Secure cookies are sent back, as in production.
    return TestClient(app, base_url="https://testserver")


def with_csrf(client: TestClient) -> TestClient:
    client.headers[CSRF_HEADER] = client.cookies[CSRF_COOKIE]
    return client


@pytest.fixture
def make_user(app) -> Callable[..., TestClient]:
    """Return a factory producing a logged-in client for a new user."""
    counter = iter(range(1000))

    def factory(email: str | None = None) -> TestClient:
        c = TestClient(app, base_url="https://testserver")
        email = email or f"user{next(counter)}@example.com"
        r = c.post(
            f"{API}/auth/register", json={"email": email, "password": PASSWORD, "consent": True}
        )
        assert r.status_code == 201, r.text
        return with_csrf(c)

    return factory
