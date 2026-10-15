"""meal types

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-15 15:29:07.988094

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0012'
down_revision: Union[str, Sequence[str], None] = '0011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Meal category; existing entries stay uncategorized (NULL)."""
    op.add_column("meal_logs", sa.Column("meal_type", sa.String(length=9), nullable=True))
    op.create_check_constraint(
        "mealtype", "meal_logs", "meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')"
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_meal_logs_mealtype"), "meal_logs", type_="check")
    op.drop_column("meal_logs", "meal_type")
