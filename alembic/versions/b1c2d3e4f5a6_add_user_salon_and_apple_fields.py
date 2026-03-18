"""add_user_salon_and_apple_fields

Revision ID: b1c2d3e4f5a6
Revises: ae4721e425b2
Create Date: 2026-03-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'ae4721e425b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add salon profile and Apple Calendar fields to users table."""
    op.add_column('users', sa.Column('salon_name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True))
    op.add_column('users', sa.Column('salon_slug', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True))
    op.add_column('users', sa.Column('salon_address', sqlmodel.sql.sqltypes.AutoString(length=300), nullable=True))
    op.add_column('users', sa.Column('apple_id', sqlmodel.sql.sqltypes.AutoString(length=200), nullable=True))
    op.add_column('users', sa.Column('apple_password_encrypted', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('users', sa.Column('apple_calendar_name', sqlmodel.sql.sqltypes.AutoString(length=200), nullable=True))
    op.create_index(op.f('ix_users_salon_slug'), 'users', ['salon_slug'], unique=False)


def downgrade() -> None:
    """Remove salon profile and Apple Calendar fields from users table."""
    op.drop_index(op.f('ix_users_salon_slug'), table_name='users')
    op.drop_column('users', 'apple_calendar_name')
    op.drop_column('users', 'apple_password_encrypted')
    op.drop_column('users', 'apple_id')
    op.drop_column('users', 'salon_address')
    op.drop_column('users', 'salon_slug')
    op.drop_column('users', 'salon_name')
