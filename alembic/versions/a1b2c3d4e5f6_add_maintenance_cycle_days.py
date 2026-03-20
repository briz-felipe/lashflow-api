"""add maintenance_cycle_days to users

Revision ID: a1b2c3d4e5f6
Revises: f5a6b7c8d9e0
Create Date: 2026-03-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'f5a6b7c8d9e0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('maintenance_cycle_days', sa.Integer(), nullable=False, server_default='15'))


def downgrade() -> None:
    op.drop_column('users', 'maintenance_cycle_days')
