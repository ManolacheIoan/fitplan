"""Offset pagination without a COUNT query: fetch one extra row to know if more exist."""

from collections.abc import Sequence
from typing import Annotated

from fastapi import Query
from pydantic import BaseModel

Limit = Annotated[int, Query(ge=1, le=50)]
Offset = Annotated[int, Query(ge=0, le=100_000)]


class Page[T](BaseModel):
    items: list[T]
    next_offset: int | None


def page_of[T](rows: Sequence[T], limit: int, offset: int) -> tuple[list[T], int | None]:
    """`rows` must have been queried with LIMIT limit + 1."""
    has_more = len(rows) > limit
    return list(rows[:limit]), (offset + limit if has_more else None)
