"""english plan day names

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-15 14:48:59.770642

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0010'
down_revision: Union[str, Sequence[str], None] = '0009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Day names of already generated plans: Romanian -> English (an optional " A"/" B"/" C"
# suffix is kept). Mirrors the names now used in app/plans/constants.py.
NAMES = [
    ("Corp întreg", "Full Body"),
    ("Superior", "Upper"),
    ("Inferior", "Lower"),
    ("Împingere", "Push"),
    ("Tracțiune", "Pull"),
    ("Picioare", "Legs"),
    ("Piept", "Chest"),
    ("Spate", "Back"),
    ("Umeri", "Shoulders"),
    ("Brațe", "Arms"),
]

RENAME = sa.text(
    "UPDATE plan_days SET name = :new || substr(name, length(:old) + 1) "
    "WHERE name = :old OR name IN (:old || ' A', :old || ' B', :old || ' C')"
)


def upgrade() -> None:
    for old, new in NAMES:
        op.get_bind().execute(RENAME, {"old": old, "new": new})


def downgrade() -> None:
    for old, new in NAMES:
        op.get_bind().execute(RENAME, {"old": new, "new": old})
