"""add_appointment_id_to_anamneses

Revision ID: j9k0l1m2n3o4
Revises: i8j9k0l1m2n3
Create Date: 2026-03-26 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "j9k0l1m2n3o4"
down_revision: Union[str, None] = "i8j9k0l1m2n3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("anamneses", sa.Column("appointment_id", sa.Uuid(), nullable=True))
    op.create_index("ix_anamneses_appointment_id", "anamneses", ["appointment_id"])


def downgrade() -> None:
    op.drop_index("ix_anamneses_appointment_id", table_name="anamneses")
    op.drop_column("anamneses", "appointment_id")
