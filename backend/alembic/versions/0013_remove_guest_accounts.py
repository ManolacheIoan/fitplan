"""remove guest accounts

Guest mode is removed: every account has an email and a password. Existing guest accounts
are deleted with all their data (ON DELETE CASCADE), as their temporary nature promised.

Revision ID: 0013
Revises: 0012
Create Date: 2026-10-25 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0013'
down_revision: Union[str, Sequence[str], None] = '0012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("DELETE FROM users WHERE is_guest")
    op.drop_constraint(op.f("ck_users_credentials"), "users", type_="check")
    op.alter_column('users', 'password_hash',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(length=254),
               nullable=False)
    op.drop_column('users', 'is_guest')


def downgrade() -> None:
    """Downgrade schema (deleted guest accounts are not restored)."""
    op.add_column('users', sa.Column('is_guest', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(length=254),
               nullable=True)
    op.alter_column('users', 'password_hash',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)
    op.create_check_constraint(
        "credentials", "users", "is_guest OR (email IS NOT NULL AND password_hash IS NOT NULL)"
    )
