"""add_removal_application_service_type

Revision ID: g6h7i8j9k0l1
Revises: f5a6b7c8d9e0
Create Date: 2026-03-20 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'g6h7i8j9k0l1'
down_revision: Union[str, Sequence[str], None] = 'f5a6b7c8d9e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    # PostgreSQL: add new value to existing enum type
    if bind.dialect.name == 'postgresql':
        bind.execute(sa.text("ALTER TYPE lashservicetype ADD VALUE IF NOT EXISTS 'removal_application'"))


def downgrade() -> None:
    # PostgreSQL does not support removing values from an enum type without recreating it.
    # This downgrade is intentionally a no-op to avoid data loss.
    pass
