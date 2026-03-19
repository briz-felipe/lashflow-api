"""add_user_salon_and_apple_fields

Revision ID: b1c2d3e4f5a6
Revises: ae4721e425b2
Create Date: 2026-03-18 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op


revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'ae4721e425b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE users
            ADD COLUMN IF NOT EXISTS salon_name    VARCHAR(200),
            ADD COLUMN IF NOT EXISTS salon_slug    VARCHAR(100),
            ADD COLUMN IF NOT EXISTS salon_address TEXT,
            ADD COLUMN IF NOT EXISTS apple_id      VARCHAR(200),
            ADD COLUMN IF NOT EXISTS apple_password_encrypted TEXT,
            ADD COLUMN IF NOT EXISTS apple_calendar_name      VARCHAR(200)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_users_salon_slug ON users (salon_slug)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_users_salon_slug")
    op.execute("""
        ALTER TABLE users
            DROP COLUMN IF EXISTS apple_calendar_name,
            DROP COLUMN IF EXISTS apple_password_encrypted,
            DROP COLUMN IF EXISTS apple_id,
            DROP COLUMN IF EXISTS salon_address,
            DROP COLUMN IF EXISTS salon_slug,
            DROP COLUMN IF EXISTS salon_name
    """)
