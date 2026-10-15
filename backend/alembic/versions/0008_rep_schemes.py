"""rep schemes

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-15 14:31:34.861398

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0008'
down_revision: Union[str, Sequence[str], None] = '0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMES = "'strength', 'compound', 'isolation', 'bodyweight_hard', 'calves', 'core', 'timed'"


def upgrade() -> None:
    """Per-exercise rep schemes; reps may be seconds for timed exercises."""
    # Existing rows get a temporary value; `python -m seed` sets the real scheme per exercise.
    op.add_column(
        "exercises",
        sa.Column("rep_scheme", sa.String(length=15), server_default="compound", nullable=False),
    )
    op.alter_column("exercises", "rep_scheme", server_default=None)
    op.create_check_constraint("repscheme", "exercises", f"rep_scheme IN ({SCHEMES})")

    op.drop_constraint(op.f("ck_plan_exercises_reps"), "plan_exercises", type_="check")
    op.create_check_constraint(
        "reps", "plan_exercises", "reps_min >= 1 AND reps_min <= reps_max AND reps_max <= 120"
    )
    op.drop_constraint(op.f("ck_set_logs_reps_range"), "set_logs", type_="check")
    op.create_check_constraint("reps_range", "set_logs", "reps BETWEEN 1 AND 300")


def downgrade() -> None:
    op.drop_constraint(op.f("ck_set_logs_reps_range"), "set_logs", type_="check")
    op.create_check_constraint("reps_range", "set_logs", "reps BETWEEN 1 AND 100")
    op.drop_constraint(op.f("ck_plan_exercises_reps"), "plan_exercises", type_="check")
    op.create_check_constraint(
        "reps", "plan_exercises", "reps_min >= 1 AND reps_min <= reps_max AND reps_max <= 30"
    )
    op.drop_constraint(op.f("ck_exercises_repscheme"), "exercises", type_="check")
    op.drop_column("exercises", "rep_scheme")
