"""program choice

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-15 14:27:55.218889

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0007'
down_revision: Union[str, Sequence[str], None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PROGRAMS = "'auto', 'full_body', 'upper_lower', 'push_pull_legs', 'bro_split'"
OLD_TEMPLATES = "'full_body', 'upper_lower', 'push_pull_legs'"
NEW_TEMPLATES = "'full_body', 'upper_lower', 'push_pull_legs', 'bro_split'"


def upgrade() -> None:
    """Program choice on the profile; bro split template."""
    op.add_column(
        "profiles",
        sa.Column("program", sa.String(length=14), server_default="auto", nullable=False),
    )
    op.create_check_constraint("program", "profiles", f"program IN ({PROGRAMS})")
    op.drop_constraint(op.f("ck_plans_template"), "plans", type_="check")
    op.create_check_constraint("template", "plans", f"template IN ({NEW_TEMPLATES})")


def downgrade() -> None:
    op.drop_constraint(op.f("ck_plans_template"), "plans", type_="check")
    op.create_check_constraint("template", "plans", f"template IN ({OLD_TEMPLATES})")
    op.drop_constraint(op.f("ck_profiles_program"), "profiles", type_="check")
    op.drop_column("profiles", "program")
