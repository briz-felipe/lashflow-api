"""add_expense_id_to_stock_movements

Revision ID: i8j9k0l1m2n3
Revises: h7i8j9k0l1m2
Create Date: 2026-03-25 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "i8j9k0l1m2n3"
down_revision: Union[str, None] = "h7i8j9k0l1m2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("stock_movements", sa.Column("expense_id", sa.Uuid(), nullable=True))
    op.create_index("ix_stock_movements_expense_id", "stock_movements", ["expense_id"])


def downgrade() -> None:
    op.drop_index("ix_stock_movements_expense_id", table_name="stock_movements")
    op.drop_column("stock_movements", "expense_id")
