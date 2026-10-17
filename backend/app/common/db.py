"""Database engine, declarative base and the request-scoped session dependency."""

from collections.abc import Iterator
from enum import StrEnum
from functools import lru_cache

from sqlalchemy import Engine, Enum, MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

# Deterministic constraint names keep Alembic migrations stable.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def str_enum(cls: type[StrEnum]) -> Enum:
    """Enum column stored as VARCHAR + CHECK constraint (simpler migrations than PG enums)."""
    return Enum(
        cls,
        native_enum=False,
        create_constraint=True,
        length=max(len(m.value) for m in cls),
        values_callable=lambda e: [m.value for m in e],
    )


@lru_cache
def get_engine() -> Engine:
    # Small pool: free-tier Postgres limits connections. pre_ping recovers after Neon autosuspend.
    # hide_parameters: SQL errors never carry the bound values (weights, birth dates...).
    return create_engine(
        get_settings().database_url,
        pool_size=5,
        max_overflow=2,
        pool_pre_ping=True,
        hide_parameters=True,
    )


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_db() -> Iterator[Session]:
    with get_sessionmaker()() as session:
        yield session
