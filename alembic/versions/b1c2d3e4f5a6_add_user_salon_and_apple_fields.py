"""add_user_salon_and_apple_fields

Revision ID: b1c2d3e4f5a6
Revises: ae4721e425b2
Create Date: 2026-03-18 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'ae4721e425b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    result = bind.execute(sa.text(f"PRAGMA table_info({table})"))
    return any(row[1] == column for row in result)


def upgrade() -> None:
    if not _column_exists('users', 'salon_name'):
        op.add_column('users', sa.Column('salon_name', sa.String(200), nullable=True))
    if not _column_exists('users', 'salon_slug'):
        op.add_column('users', sa.Column('salon_slug', sa.String(100), nullable=True))
    if not _column_exists('users', 'salon_address'):
        op.add_column('users', sa.Column('salon_address', sa.Text(), nullable=True))
    if not _column_exists('users', 'apple_id'):
        op.add_column('users', sa.Column('apple_id', sa.String(200), nullable=True))
    if not _column_exists('users', 'apple_password_encrypted'):
        op.add_column('users', sa.Column('apple_password_encrypted', sa.Text(), nullable=True))
    if not _column_exists('users', 'apple_calendar_name'):
        op.add_column('users', sa.Column('apple_calendar_name', sa.String(200), nullable=True))

    # Create index only if not exists (SQLite-safe)
    bind = op.get_bind()
    indexes = bind.execute(sa.text("SELECT name FROM sqlite_master WHERE type='index' AND name='ix_users_salon_slug'")).fetchall()
    if not indexes:
        op.create_index('ix_users_salon_slug', 'users', ['salon_slug'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    indexes = bind.execute(sa.text("SELECT name FROM sqlite_master WHERE type='index' AND name='ix_users_salon_slug'")).fetchall()
    if indexes:
        op.drop_index('ix_users_salon_slug', table_name='users')
    # SQLite does not support DROP COLUMN in older versions; skip for safety
