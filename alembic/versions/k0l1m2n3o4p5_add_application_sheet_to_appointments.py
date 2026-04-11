"""add_application_sheet_to_appointments

Revision ID: k0l1m2n3o4p5
Revises: j9k0l1m2n3o4
Create Date: 2026-04-11 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "k0l1m2n3o4p5"
down_revision: Union[str, None] = "j9k0l1m2n3o4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = {c["name"] for c in inspector.get_columns("appointments")}
    if "application_sheet" not in existing:
        op.add_column("appointments", sa.Column("application_sheet", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("appointments", "application_sheet")
