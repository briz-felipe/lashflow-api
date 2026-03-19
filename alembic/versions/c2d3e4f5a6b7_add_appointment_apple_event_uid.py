"""add_appointment_apple_event_uid

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-03-18 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, Sequence[str], None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = {c["name"] for c in inspector.get_columns("appointments")}
    if "apple_event_uid" not in existing:
        op.add_column("appointments", sa.Column("apple_event_uid", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("appointments", "apple_event_uid")
